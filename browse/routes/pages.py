"""Coauthored's own information pages: about, help, policies, terms, privacy, contact.

These replace upstream's redirects to arXiv's help site."""
from typing import Any

from flask import Blueprint, render_template

blueprint = Blueprint("pages", __name__)

PAGES = {
    "/about": ("pages/about.html", "About Coauthored"),
    "/help": ("pages/help/index.html", "Help"),
    "/help/submit": ("pages/help/submit.html", "How to submit"),
    "/help/identifiers": ("pages/help/identifiers.html", "Identifiers and citing"),
    "/help/categories": ("pages/help/categories.html", "Categories"),
    "/policies/ai-authorship": ("pages/policies/ai_authorship.html", "AI authorship policy"),
    "/policies/moderation": ("pages/policies/moderation.html", "Moderation policy"),
    "/policies/licenses": ("pages/policies/licenses.html", "Licences"),
    "/licenses/nonexclusive-distrib/1.0/": ("pages/policies/nonexclusive.html",
                                            "Coauthored non-exclusive distribution licence 1.0"),
    "/terms": ("pages/terms.html", "Terms of use"),
    "/privacy": ("pages/privacy.html", "Privacy policy"),
    "/contact": ("pages/contact.html", "Contact"),
    "/accessibility": ("pages/accessibility.html", "Accessibility"),
}


def _view(template: str, title: str) -> Any:
    def view() -> Any:
        return render_template(template, page_title=title)
    return view


for _path, (_template, _title) in PAGES.items():
    blueprint.add_url_rule(_path, endpoint=_path.strip("/").replace("/", "_").replace(".", "_") or "root",
                           view_func=_view(_template, _title))
