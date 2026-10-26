import re

import frappe
from frappe.utils import strip_html_tags
from frappe.website.utils import cleanup_page_name
from redis.exceptions import ResponseError
from textblob import TextBlob
from textblob.exceptions import MissingCorpusError

from helpdesk.helpdesk.doctype.hd_article.hd_article import make_article_filters
from helpdesk.search import NUM_RESULTS, get_stopwords
from helpdesk.search import search as hd_search

RELATED_LIMIT = 3
EXCERPT_LENGTH = 160


def get_nouns(blob: TextBlob):
    try:
        return [word for word, pos in blob.pos_tags if pos[0] == "N"]
    except LookupError, MissingCorpusError:
        return []


def get_noun_phrases(blob: TextBlob):
    try:
        return blob.noun_phrases
    except LookupError, MissingCorpusError:
        return []


def search_with_enough_results(
    prev_res: list, query: str, qtype="and", limit: int = NUM_RESULTS
) -> tuple[list, bool]:
    out = hd_search(query, qtype=qtype, limit=limit)
    if not out:
        return prev_res, len(prev_res) >= NUM_RESULTS
    articles = {}
    for item in prev_res + filter_accessible_articles(out[0].get("items", [])):
        articles.setdefault(item["name"].split("#")[0], item)
    items = list(articles.values())[:limit]
    return items, len(items) >= NUM_RESULTS


def filter_accessible_articles(articles: list) -> list:
    """The index can be stale and holds every visibility."""
    names = {article["name"].split("#")[0] for article in articles}
    if not names:
        return []
    published = frappe.get_all(
        "HD Article",
        filters=make_article_filters(name=("in", list(names))),
        pluck="name",
    )
    return [
        article for article in articles if article["name"].split("#")[0] in published
    ]


def sanitize_query(query: str) -> str:
    q = query.strip().lower()
    q = re.sub(r"[^a-z0-9\s]", " ", q)
    # Collapse multiple spaces into one
    q = re.sub(r"\s+", " ", q)
    return q.strip()


@frappe.whitelist()
def get_article_stats(article_name: str):
    if not frappe.db.exists("HD Article", article_name):
        raise frappe.PermissionError
    frappe.has_permission("HD Article", "read", article_name, throw=True)
    views = frappe.db.get_value("HD Article", article_name, "views")

    likes = frappe.db.count(
        "HD Article Feedback",
        filters={
            "article": article_name,
            "feedback": 1,
        },
    )

    dislikes = frappe.db.count(
        "HD Article Feedback",
        filters={
            "article": article_name,
            "feedback": 2,
        },
    )

    return {
        "views": views,
        "likes": likes,
        "dislikes": dislikes,
    }


@frappe.whitelist()
def search(query: str, limit: int = NUM_RESULTS) -> list:
    query = sanitize_query(query)
    ret, enough = search_with_enough_results([], query, limit=limit)
    if enough:
        return ret
    blob = TextBlob(query)  # fallback
    if noun_phrases := get_noun_phrases(blob):
        query = " ".join(noun_phrases)
        ret, enough = search_with_enough_results(ret, query, limit=limit)
        if enough:
            return ret
        ret, enough = search_with_enough_results(ret, query, qtype="or", limit=limit)
        if enough:
            return ret
    if nouns := get_nouns(blob):
        query = " ".join(nouns)
        ret, enough = search_with_enough_results(ret, query, limit=limit)
        if enough:
            return ret
        ret, enough = search_with_enough_results(ret, query, qtype="or", limit=limit)
    return ret


@frappe.whitelist()
def get_related(query: str) -> list[dict]:
    return [
        {
            "name": row["name"],
            "title": strip_html_tags(row["title"]),
            "title_slug": row["title_slug"],
        }
        for row in search_accessible_articles(query)[:RELATED_LIMIT]
    ]


def search_accessible_articles(query: str, limit: int = NUM_RESULTS) -> list[dict]:
    """Empty without RediSearch or its index."""
    words = sanitize_query(query).split()
    if words and set(words) <= set(get_stopwords()):
        return search_titles(words, limit)
    try:
        hits = search(query, limit)
    except ResponseError:
        return []
    articles = {}
    for hit in hits:
        name = hit["name"].split("#")[0]
        articles.setdefault(
            name,
            {
                "name": name,
                "title": _as_mark(hit.get("subject")),
                # slug from the unmarked subject
                "title_slug": cleanup_page_name(
                    strip_html_tags(hit.get("subject") or "")
                ),
                "excerpt": _as_mark(hit.get("description")),
            },
        )
    return list(articles.values())


def search_titles(words: list[str], limit: int = NUM_RESULTS) -> list[dict]:
    """Stopwords aren't indexed, so "what" alone reads titles instead."""
    filters = [
        [field, *(value if isinstance(value, list | tuple) else ("=", value))]
        for field, value in make_article_filters().items()
    ]
    filters += [["title", "like", f"%{word}%"] for word in words]
    return [
        {
            "name": row.name,
            "title": row.title,
            "title_slug": cleanup_page_name(row.title),
            "excerpt": strip_html_tags(row.content or "")[:EXCERPT_LENGTH],
        }
        for row in frappe.get_all(
            "HD Article",
            filters=filters,
            fields=["name", "title", "content"],
            order_by="views desc",
            limit=limit,
        )
    ]


def _as_mark(text: str | None) -> str:
    return (text or "").replace("<b>", "<mark>").replace("</b>", "</mark>")
