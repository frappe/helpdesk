"""Release notes shown to agents in the "What's new" sidebar card and modal.

Each note is a Markdown file in `helpdesk/whats_new/` that starts with flat
`key: value` frontmatter:

    ---
    title: A short headline          (required)
    version: unreleased | 1.2.3      (a release stamps `unreleased` with its version)
    date: 2026-01-31                 (set when the note is released)
    media: name.png | name.mp4       (optional, a file in helpdesk/public/whats_new/;
                                      `name.dark.png` is used in dark mode if present)
    ---
    The body, in Markdown.

The file name is the note's id. What each user has seen is kept as a list of ids.
"""

import json
from functools import cache
from pathlib import Path

import frappe
from frappe.utils import md_to_html

APP_DIR = Path(__file__).parent
NOTES_DIR = APP_DIR / "whats_new"
MEDIA_DIR = APP_DIR / "public" / "whats_new"
MEDIA_URL = "/assets/helpdesk/whats_new"
VIDEO_EXTENSIONS = {".mp4", ".webm"}
SEEN_KEY = "helpdesk_whats_new_seen"
UNRELEASED = "unreleased"


@cache
def load_notes() -> list[dict]:
    """All notes, newest first: unreleased ones, then by version, then by title."""
    notes = []
    for path in sorted(NOTES_DIR.glob("*.md")):
        note = parse_note(path)
        if note:
            notes.append(note)
    notes.sort(key=lambda note: note["title"])
    notes.sort(key=lambda note: version_key(note["version"]), reverse=True)
    return notes


def parse_note(path: Path) -> dict | None:
    """The note in `path`, or None (after logging) when it has no title or frontmatter."""
    try:
        meta, body = split_frontmatter(path.read_text())
        title = meta.get("title")
        if not title:
            raise ValueError("a note needs a title")
        version = meta.get("version") or UNRELEASED
        released = version != UNRELEASED
        return {
            "id": path.stem,
            "title": title,
            "version": version if released else None,
            "date": meta.get("date") if released else None,
            "media": resolve_media(meta.get("media")),
            "body": md_to_html(body.strip()) or "",
        }
    except Exception:
        frappe.log_error(title=f"Skipped What's new note {path.name}")
        return None


def split_frontmatter(text: str) -> tuple[dict, str]:
    """Split `---` fenced `key: value` lines from the Markdown body that follows."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        raise ValueError("a note must start with frontmatter")
    end = next(i for i, line in enumerate(lines[1:], 1) if line.strip() == "---")
    meta = {}
    for line in lines[1:end]:
        key, _, value = line.partition(":")
        if key.strip():
            meta[key.strip()] = value.strip()
    return meta, "\n".join(lines[end + 1 :])


def resolve_media(name: str | None) -> dict | None:
    """Urls of the picture or video `name` in the media folder, or None when it is
    not a plain file name of an existing file."""
    if not name or Path(name).name != name or not (MEDIA_DIR / name).is_file():
        return None
    file = Path(name)
    dark = f"{file.stem}.dark{file.suffix}"
    return {
        "url": f"{MEDIA_URL}/{name}",
        "dark_url": f"{MEDIA_URL}/{dark}" if (MEDIA_DIR / dark).is_file() else None,
        "kind": "video" if file.suffix.lower() in VIDEO_EXTENSIONS else "image",
    }


def version_key(version: str | None) -> tuple:
    """Sort key where unreleased beats any version and parts that are not numbers count as 0."""
    if not version:
        return (1, ())
    parts = tuple(int(p) if p.isdigit() else 0 for p in version.split("."))
    return (0, parts)


def group_by_release(notes: list[dict]) -> list[dict]:
    """Group consecutive notes of the same version into `{version, date, notes}`."""
    releases = []
    for note in notes:
        if not releases or releases[-1]["version"] != note["version"]:
            releases.append(
                {"version": note["version"], "date": note["date"], "notes": []}
            )
        releases[-1]["notes"].append(note)
    return releases


def get_unseen_notes(user: str | None = None) -> list[dict]:
    """Notes whose id is not in `user`'s seen list."""
    seen = get_seen_ids(user)
    return [note for note in load_notes() if note["id"] not in seen]


def mark_all_seen(user: str | None = None) -> None:
    """Record every current note as seen by `user`."""
    ids = json.dumps([note["id"] for note in load_notes()])
    frappe.defaults.set_user_default(SEEN_KEY, ids, user or frappe.session.user)


def get_seen_ids(user: str | None = None) -> set[str]:
    value = frappe.defaults.get_user_default(SEEN_KEY, user or frappe.session.user)
    try:
        return set(json.loads(value)) if value else set()
    except (TypeError, ValueError):
        return set()
