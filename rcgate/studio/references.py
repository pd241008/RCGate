"""Curated offline references. None of these are RC-Gate scoring inputs."""

from __future__ import annotations

import json
from pathlib import Path

from ..paths import PROJECT_ROOT

DEFAULT_PATH = PROJECT_ROOT / "demo_fixtures" / "independent_references.json"

REQUIRED = (
    "id",
    "source_id",
    "title",
    "publisher",
    "url",
    "excerpt",
    "verified_on",
    "relevance",
    "used_in_rcgate_score",
)

EMPTY_NOTE = (
    "No independent reference is attached to this item yet. "
    "The score uses the supplied task context and the existing RC-Gate features; "
    "it does not include a separately retrieved reference."
)

SEPARATION_NOTE = (
    "These pages were saved for your own checking. They were not retrieved for the "
    "original models, and they are not an input to the RC-Gate score."
)


def load_references(path: Path | None = None) -> list[dict]:
    """Load the manifest. A reference marked as a scoring input is rejected."""
    file_path = Path(path or DEFAULT_PATH)
    if not file_path.exists():
        return []
    payload = json.loads(file_path.read_text(encoding="utf-8"))
    rows = payload.get("references", [])
    if not isinstance(rows, list):
        raise ValueError("independent_references.json references must be a list")
    checked: list[dict] = []
    seen: set[str] = set()
    for row in rows:
        missing = [key for key in REQUIRED if key not in row]
        if missing:
            raise ValueError(f"reference missing {missing}")
        if row["used_in_rcgate_score"] is not False:
            raise ValueError(
                f"reference {row.get('id')} must set used_in_rcgate_score to false"
            )
        url = str(row["url"])
        if not url.startswith("https://"):
            raise ValueError(f"reference {row.get('id')} needs an https URL")
        if not str(row["excerpt"]).strip() or not str(row["title"]).strip():
            raise ValueError(f"reference {row.get('id')} needs a title and excerpt")
        if str(row["id"]) in seen:
            raise ValueError(f"duplicate reference id {row['id']}")
        seen.add(str(row["id"]))
        checked.append(dict(row))
    return checked


def references_for(rows: list[dict], source_id: str) -> list[dict]:
    return [row for row in rows if str(row.get("source_id")) == str(source_id)]
