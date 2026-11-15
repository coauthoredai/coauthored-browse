"""Browse's side of docs/CONTRACT.md: a paper published exactly as the contract says
(classic rows, coauthored_contributors, PDFs at the ftp/ and orig/ paths) is served."""
from datetime import date, datetime, timezone
from pathlib import Path

import pytest
from bs4 import BeautifulSoup
from sqlalchemy import insert, text
from sqlalchemy.orm import Session as OrmSession

from arxiv.db.models import Document, DocumentCategory, Metadata, Updates, t_arXiv_in_category
from arxiv.files.key_patterns import current_pdf_path, previous_pdf_path
from arxiv.identifier import Identifier

from browse.factory import create_web_app
import browse.services.documents as documents
import browse.services.listing as listing

from .test_coauthored_contributors import DDL

PID = "2611.00001"
CC_BY = "http://creativecommons.org/licenses/by/4.0/"
V1_PDF = b"%PDF-1.7\n% version one\n"
V2_PDF = b"%PDF-1.7\n% version two, longer\n"


def _publish(engine, store: Path) -> None:
    """Write two versions of PID the way coauthored-submit's announce does."""
    t1 = datetime(2026, 11, 16, 20, 0, tzinfo=timezone.utc)
    t2 = datetime(2026, 11, 18, 20, 0, tzinfo=timezone.utc)
    common = dict(paper_id=PID, submitter_id=None, submitter_name="Ada Researcher",
                  submitter_email="ada@example.org", source_format="pdf", source_flags="",
                  title="A Solved Game", authors="Ada Researcher, Claude",
                  abs_categories="cs.GT math.CO", comments=None, license=CC_BY,
                  abstract="We solve a small game.", is_withdrawn=0)
    with OrmSession(engine) as s:
        doc = Document(paper_id=PID, title="A Solved Game", authors="Ada Researcher, Claude",
                       submitter_email="ada@example.org", submitter_id=None,
                       dated=int(t1.timestamp()), primary_subject_class="cs.GT",
                       created=t1.replace(tzinfo=None))
        s.add(doc)
        s.flush()
        s.add(Metadata(document_id=doc.document_id, version=1, created=t1.replace(tzinfo=None),
                       updated=t1.replace(tzinfo=None), source_size=len(V1_PDF), is_current=0,
                       modtime=int(t1.timestamp()), published_at=t1.replace(tzinfo=None), **common))
        s.add(Metadata(document_id=doc.document_id, version=2, created=t2.replace(tzinfo=None),
                       updated=t2.replace(tzinfo=None), source_size=len(V2_PDF), is_current=1,
                       modtime=int(t2.timestamp()), published_at=t2.replace(tzinfo=None), **common))
        s.add(DocumentCategory(document_id=doc.document_id, category="cs.GT", is_primary=1))
        s.add(DocumentCategory(document_id=doc.document_id, category="math.CO", is_primary=0))
        s.execute(insert(t_arXiv_in_category), [
            dict(document_id=doc.document_id, archive="cs", subject_class="GT", is_primary=1),
            dict(document_id=doc.document_id, archive="math", subject_class="CO", is_primary=0)])
        for v, d, action in ((1, date(2026, 11, 16), "new"), (2, date(2026, 11, 18), "replace")):
            for arch, cat in (("cs", "cs.GT"), ("math", "math.CO")):
                s.add(Updates(document_id=doc.document_id, version=v, date=d, action=action,
                              archive=arch, category=cat))
        s.execute(text(DDL))
        for v in (1, 2):
            s.execute(text("INSERT INTO coauthored_contributors VALUES"
                           " (:p, :v, 1, 'Ada Researcher', 'human', NULL, NULL, NULL, NULL, 'Posed the problem.', 1),"
                           " (:p, :v, 2, 'Claude', 'ai', NULL, 'Claude', 'Opus 5.5', 'Anthropic', 'Wrote the solver.', 0)"),
                      {"p": PID, "v": v})
        s.commit()
    current = store / current_pdf_path(Identifier(PID))
    previous = store / previous_pdf_path(Identifier(f"{PID}v1"))
    for path, data in ((current, V2_PDF), (previous, V1_PDF)):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    (store / "reasons.json").write_text("{}")  # required at the store root (CONTRACT.md)


def _unpublish(engine) -> None:
    with engine.begin() as c:
        ids = [r[0] for r in c.execute(text("SELECT document_id FROM arXiv_documents WHERE paper_id = :p"), {"p": PID})]
        for table in ("arXiv_updates", "arXiv_in_category", "arXiv_document_category", "arXiv_metadata", "arXiv_documents"):
            for i in ids:
                c.execute(text(f"DELETE FROM {table} WHERE document_id = :i"), {"i": i})
        c.execute(text("DELETE FROM coauthored_contributors WHERE paper_id = :p"), {"p": PID})


@pytest.fixture
def contract_client(loaded_db_copy, reset_packages, tmp_path):
    from tests.conftest import test_config
    import arxiv.legacy.papers.dissemination.reasons as reasons
    reasons._reasons_data = None
    from arxiv.db import Session
    conf = test_config()
    conf.update({
        "CLASSIC_DB_URI": loaded_db_copy[0], "LATEXML_DB_URI": loaded_db_copy[1],
        "DOCUMENT_ABSTRACT_SERVICE": documents.db_docs,
        "DOCUMENT_LISTING_SERVICE": listing.db_listing,
        "DISSEMINATION_STORAGE_PREFIX": f"{tmp_path}/", "SOURCE_STORAGE_PREFIX": f"{tmp_path}/",
        "ABS_PATH_ROOT": f"{tmp_path}/", "LATEXML_ENABLED": 0,
    })
    app = create_web_app(**conf)
    # Write into the database the app's session actually uses (in these tests, the
    # session-scoped test database), and remove the paper afterwards.
    engine = Session.get_bind(mapper=Metadata)
    _publish(engine, tmp_path)
    try:
        with app.app_context():
            yield app.test_client()
    finally:
        _unpublish(engine)


def test_abs_page_of_contract_paper(contract_client):
    rv = contract_client.get(f"/abs/{PID}")
    assert rv.status_code == 200
    html = BeautifulSoup(rv.data.decode(), "html.parser")
    assert "A Solved Game" in html.find("h1", class_="title").get_text()
    cite = html.find("td", class_="arxivid").get_text()
    assert f"coauthored:{PID}" in cite and "arXiv" not in cite
    assert html.find("span", class_="ca-ai-badge") is not None
    assert "Wrote the solver." in html.find("div", class_="ca-contributions").get_text()
    assert "[v2]" in html.find("div", class_="submission-history").get_text()


def test_pdfs_of_contract_paper(contract_client):
    rv = contract_client.get(f"/pdf/{PID}")
    assert rv.status_code == 200 and rv.data == V2_PDF
    rv = contract_client.get(f"/pdf/{PID}v1")
    assert rv.status_code == 200 and rv.data == V1_PDF


def test_month_listing_has_contract_paper(contract_client):
    rv = contract_client.get("/list/cs.GT/2026-11")
    assert rv.status_code == 200
    assert f"coauthored:{PID}" in rv.data.decode()
