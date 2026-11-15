"""Coauthored's paper search: a simple database search over current versions.

arXiv runs search as a separate service (arxiv-search, on OpenSearch). At Coauthored's size a
query on the classic metadata table is enough; it can be replaced by a search index later."""
from typing import Any

from flask import Blueprint, render_template, request
from sqlalchemy import or_

from arxiv.db import Session
from arxiv.db.models import Metadata

blueprint = Blueprint("search", __name__)

FIELDS = {
    "all": ("title", "authors", "abstract", "paper_id"),
    "title": ("title",),
    "author": ("authors",),
    "abstract": ("abstract",),
    "paper_id": ("paper_id",),
}
PAGE = 50


@blueprint.route("/search")
def search() -> Any:
    query = (request.args.get("query") or "").strip()[:200]
    searchtype = request.args.get("searchtype", "all")
    if searchtype not in FIELDS:
        searchtype = "all"
    archive = (request.args.get("archive") or "").strip()[:20]
    try:
        start = max(0, int(request.args.get("start", 0)))
    except ValueError:
        start = 0
    results: list[Metadata] = []
    total = 0
    if query:
        q = Session.query(Metadata).filter(Metadata.is_current == 1)
        if query.lower().startswith("coauthored:"):
            query = query.split(":", 1)[1]
        for word in query.split()[:8]:
            pattern = f"%{word}%"
            q = q.filter(or_(*[getattr(Metadata, f).ilike(pattern) for f in FIELDS[searchtype]]))
        if archive:
            q = q.filter(or_(Metadata.abs_categories.ilike(f"{archive}%"),
                             Metadata.abs_categories.ilike(f"% {archive}%")))
        total = q.count()
        results = q.order_by(Metadata.paper_id.desc()).offset(start).limit(PAGE).all()
    return render_template("search.html", query=query, searchtype=searchtype, archive=archive,
                           results=results, total=total, start=start, page=PAGE,
                           page_title="Search")
