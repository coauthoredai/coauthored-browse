"""Coauthored's published author lists, written by coauthored-submit at announce.

The table ``coauthored_contributors`` (see CONTRACT.md in the Coauthored workspace) holds, for
each paper version, every author in order: human or AI, the AI system, version and provider,
each author's contribution, and which human authors take responsibility. Browse only reads it.
"""
import logging
from dataclasses import dataclass
from typing import List, Optional

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from arxiv.db import Session
from arxiv.db.models import Metadata

logger = logging.getLogger(__name__)

_QUERY = text(
    "SELECT position, display_name, kind, orcid, ai_system, ai_version, ai_provider,"
    " contribution, is_responsible FROM coauthored_contributors"
    " WHERE paper_id = :paper_id AND version = :version ORDER BY position"
)


@dataclass(frozen=True)
class Contributor:
    position: int
    display_name: str
    kind: str
    orcid: Optional[str]
    ai_system: Optional[str]
    ai_version: Optional[str]
    ai_provider: Optional[str]
    contribution: str
    is_responsible: bool


def get_contributors(paper_id: str, version: int) -> List[Contributor]:
    """The authors of one version, or [] if there are none (or the table is absent, as in
    upstream test data); the page then falls back to the classic author string."""
    try:
        # A text query has no mapper, so name one on the classic database for the bind.
        rows = Session.execute(_QUERY, {"paper_id": paper_id, "version": version},
                               bind_arguments={"mapper": Metadata}).all()
    except SQLAlchemyError as ex:
        logger.debug("coauthored_contributors unavailable: %s", ex)
        Session.rollback()
        return []
    return [Contributor(int(r[0]), r[1], r[2], r[3], r[4], r[5], r[6], r[7], bool(r[8])) for r in rows]
