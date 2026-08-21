# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt

import re
import unicodedata


CJK_RUN_RE = re.compile(
    r"[\u3005-\u3007\u303b\u3040-\u30ff\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]+"
)
WHITESPACE_RE = re.compile(r"\s+")


def normalize_search_text(text: str | None) -> str:
    """Normalize user input while preserving Japanese letters and numbers."""
    if not text:
        return ""

    normalized = unicodedata.normalize("NFKC", str(text)).lower()
    sanitized = "".join(
        char if char.isalnum() or char.isspace() else " " for char in normalized
    )
    return WHITESPACE_RE.sub(" ", sanitized).strip()


def contains_cjk(text: str | None) -> bool:
    return bool(text and CJK_RUN_RE.search(unicodedata.normalize("NFKC", str(text))))


def cjk_ngrams(text: str | None, sizes: tuple[int, ...] = (2, 3)) -> list[str]:
    """Return stable, unique CJK n-grams for substring search."""
    normalized = normalize_search_text(text)
    terms = []
    seen = set()

    for run in CJK_RUN_RE.findall(normalized):
        for size in sizes:
            if len(run) < size:
                continue
            for offset in range(len(run) - size + 1):
                term = run[offset : offset + size]
                if term not in seen:
                    seen.add(term)
                    terms.append(term)

    return terms


def cjk_index_terms(text: str | None) -> str:
    return " ".join(cjk_ngrams(text))


def expand_cjk_query(text: str | None) -> str:
    """Expand CJK runs into searchable terms without changing Latin terms."""
    normalized = normalize_search_text(text)

    def expand(match: re.Match) -> str:
        run = match.group(0)
        if len(run) <= 2:
            return f" {run} "
        return f" {' '.join(cjk_ngrams(run, sizes=(3,)))} "

    return WHITESPACE_RE.sub(" ", CJK_RUN_RE.sub(expand, normalized)).strip()
