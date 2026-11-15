"""Coauthored: abstract pages show the published author list with AI authors and
contributions (table coauthored_contributors, written by coauthored-submit)."""
from bs4 import BeautifulSoup
from sqlalchemy import text

from arxiv.db import Session
from arxiv.db.models import Metadata

BIND = {"mapper": Metadata}

DDL = """CREATE TABLE IF NOT EXISTS coauthored_contributors (
  paper_id VARCHAR(20) NOT NULL, version INTEGER NOT NULL, position INTEGER NOT NULL,
  display_name VARCHAR(255) NOT NULL, kind VARCHAR(8) NOT NULL, orcid VARCHAR(19),
  ai_system VARCHAR(128), ai_version VARCHAR(128), ai_provider VARCHAR(128),
  contribution TEXT NOT NULL, is_responsible BOOLEAN NOT NULL DEFAULT 0,
  PRIMARY KEY (paper_id, version, position))"""


def _add_contributors(paper_id: str, version: int) -> None:
    Session.execute(text(DDL), bind_arguments=BIND)
    rows = [
        (1, "Ada Researcher", "human", "0000-0002-1825-0097", None, None, None,
         "Posed the problem and checked the proofs.", 1),
        (2, "Claude", "ai", None, "Claude", "Opus 5.5 (claude-opus-5-5)", "Anthropic",
         "Wrote the solver and drafted the paper.", 0),
    ]
    for r in rows:
        Session.execute(text(
            "INSERT INTO coauthored_contributors VALUES (:p, :v, :pos, :n, :k, :o, :s, :ver, :prov, :c, :r)"),
            {"p": paper_id, "v": version, "pos": r[0], "n": r[1], "k": r[2], "o": r[3], "s": r[4],
             "ver": r[5], "prov": r[6], "c": r[7], "r": r[8]}, bind_arguments=BIND)
    Session.commit()


def test_abs_page_shows_ai_authors_and_contributions(dbclient):
    page = BeautifulSoup(dbclient.get('/abs/0906.2112').data.decode(), 'html.parser')
    version = int(page.find('meta', {'property': 'og:url'})['content'].rsplit('v', 1)[1])
    _add_contributors('0906.2112', version)

    rv = dbclient.get('/abs/0906.2112')
    assert rv.status_code == 200
    html = BeautifulSoup(rv.data.decode(), 'html.parser')
    authors = html.find('div', class_='authors')
    assert 'Ada Researcher' in authors.get_text()
    assert 'Claude' in authors.get_text()
    badge = authors.find('span', class_='ca-ai-badge')
    assert badge is not None and badge.get_text() == 'AI'
    assert 'Anthropic' in badge['title']

    contributions = html.find('div', class_='ca-contributions')
    assert contributions is not None
    text_ = contributions.get_text(' ')
    assert 'Wrote the solver and drafted the paper.' in text_
    assert 'Opus 5.5 (claude-opus-5-5)' in text_
    assert 'responsible author' in text_
    assert contributions.find('a', class_='ca-orcid')['href'] == 'https://orcid.org/0000-0002-1825-0097'


def test_abs_page_without_contributors_uses_classic_authors(dbclient):
    rv = dbclient.get('/abs/math/0510544')
    assert rv.status_code == 200
    html = BeautifulSoup(rv.data.decode(), 'html.parser')
    assert html.find('div', class_='ca-contributions') is None
    assert html.find('div', class_='authors').get_text().strip() != 'Authors:'


def test_disabled_arxiv_features_are_404(dbclient):
    for path in ['/tb/recent', '/stats/today', '/cookies', '/a/33510', '/repec', '/form',
                 '/institutional_banner', '/show-email/x/0906.2112']:
        assert dbclient.get(path).status_code == 404, path
    assert dbclient.get('/format/0906.2112').status_code == 200  # '/form' must not catch '/format'


def test_operator_named_on_terms_privacy_and_about(dbclient):
    for path in ('/terms', '/privacy', '/about'):
        assert 'Gideon Solutions, LLC' in dbclient.get(path).data.decode(), path
    assert 'laws of the State of North Carolina' in dbclient.get('/terms').data.decode()
