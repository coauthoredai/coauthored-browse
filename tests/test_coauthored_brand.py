"""Brand audit: rendered pages must not present arXiv's name, logo, colours or services as
Coauthored's own (arXiv's brand guidelines; the MIT licence covers the code only).

Allowed: the footer's attribution and disclaimer, and NOTICE.md. Run with ``-s`` to print
the full report; pages listed in CLEAN_PAGES must have no findings.
"""
import re
from pathlib import Path

import pytest
from bs4 import BeautifulSoup

PAGES = [
    "/",
    "/abs/0906.5132",
    "/list/chao-dyn/1995-10",
    "/year/astro-ph/2009",
    "/format/0906.5132",
    "/category_taxonomy",
    "/catchup",
    "/list/hep-ph/new",
    "/list/hep-ph/recent",
    "/archive/hep-ph",
    "/about", "/help", "/help/submit", "/help/identifiers", "/help/categories",
    "/policies/ai-authorship", "/policies/moderation", "/policies/licenses",
    "/licenses/nonexclusive-distrib/1.0/", "/terms", "/privacy", "/contact", "/accessibility",
]

# Every audited page must be clean.
CLEAN_PAGES: set[str] = set(PAGES)

ALLOWED_TEXT = [
    "Coauthored runs on software adapted from arXiv's open-source code",
    "Coauthored is not affiliated with or endorsed by arXiv.",
    # Honest references on Coauthored's own pages (about, help), not branding:
    "arXiv, most journals and most repositories do not allow an AI system to be listed as an author.",
    "which arXiv publishes under the MIT licence",
    "Coauthored identifiers are not arXiv identifiers.",
    "the same subject categories and codes as arXiv",
]
# Licence URIs come from paper metadata; upstream test papers carry arXiv's licences.
# Coauthored never offers them (CONTRACT.md), so they appear only in test data.
ALLOWED_LINK_PREFIXES = ("http://arxiv.org/licenses/",)
UPSTREAM_LINK = "https://github.com/arXiv/arxiv-browse"
TEXT_PATTERNS = {
    "arXiv in text": re.compile(r"\barxiv\b", re.I),
    "Cornell": re.compile(r"\bcornell\b", re.I),
    "Simons": re.compile(r"\bsimons\b", re.I),
}
ARXIV_DOMAIN = re.compile(r"(^|[/.@])arxiv\.org\b", re.I)


def findings(html: str) -> list[str]:
    soup = BeautifulSoup(html, "html.parser")
    out = []
    for tag in soup.find_all(True):
        for attr in ("href", "src", "content", "action"):
            val = tag.get(attr)
            if isinstance(val, str) and ARXIV_DOMAIN.search(val) and val != UPSTREAM_LINK \
                    and not val.startswith(ALLOWED_LINK_PREFIXES):
                out.append(f"link to arXiv: <{tag.name} {attr}={val[:90]}>")
    for t in soup(["script", "style"]):
        t.decompose()
    text = " ".join(soup.get_text(" ").split())
    for ok in ALLOWED_TEXT:
        text = text.replace(ok, "")
    for label, pat in TEXT_PATTERNS.items():
        for m in pat.finditer(text):
            out.append(f"{label}: ...{text[max(0, m.start() - 40):m.end() + 40]}...")
    return out


def test_brand_audit(app_with_db):
    client = app_with_db.test_client()
    report = {}
    for page in PAGES:
        rv = client.get(page)
        if rv.status_code != 200:
            report[page] = [f"status {rv.status_code}"]
            continue
        report[page] = findings(rv.data.decode("utf-8", "replace"))
    print("\nBrand audit:")
    for page, items in report.items():
        print(f"  {page}: {len(items)} finding(s)")
        for item in items[:60]:
            print(f"      {item}")
    dirty = {p: report[p] for p in CLEAN_PAGES if report.get(p)}
    assert not dirty, f"pages that should be clean have findings: {dirty}"


def test_no_arxiv_brand_colour_in_css():
    css = Path(__file__).parent.parent / "browse" / "static" / "css"
    hits = [p.name for p in css.glob("*.css") if re.search(r"#b31b1b", p.read_text(errors="replace"), re.I)]
    print("\nCSS files still using arXiv's red (#B31B1B):", hits)
    assert not hits
