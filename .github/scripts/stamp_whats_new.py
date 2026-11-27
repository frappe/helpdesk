"""Stamp unreleased What's new notes with the release they ship in.

Usage: stamp_whats_new.py <version> <date>
"""

import sys
from pathlib import Path

NOTES_DIR = Path(__file__).parents[2] / "helpdesk" / "whats_new"


def stamp(source: str, version: str, date: str) -> str | None:
    """`source` with its frontmatter set to `version` and `date`, or None when it
    has no frontmatter or is not `version: unreleased`."""
    lines = source.split("\n")
    fences = [line.strip() for line in lines]
    if fences[0] != "---" or "---" not in fences[1:]:
        return None
    end = fences.index("---", 1)
    head = lines[1:end]
    if "version: unreleased" not in [line.strip() for line in head]:
        return None
    stamped = []
    for line in head:
        if line.startswith("date:"):
            continue
        stamped.append(line)
        if line.strip() == "version: unreleased":
            stamped[-1] = f"version: {version}"
            stamped.append(f"date: {date}")
    return "\n".join([lines[0], *stamped, *lines[end:]])


def main(version: str, date: str) -> None:
    for path in sorted(NOTES_DIR.glob("*.md")):
        stamped = stamp(path.read_text(), version, date)
        if stamped is not None:
            path.write_text(stamped)
            print(path)


if __name__ == "__main__":
    main(*sys.argv[1:3])
