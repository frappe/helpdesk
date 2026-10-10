import re

import frappe
from frappe.utils import strip_html_tags
from textblob import TextBlob
from textblob.exceptions import MissingCorpusError

from helpdesk.search import NUM_RESULTS
from helpdesk.search import search as hd_search
from helpdesk.search_sqlite import HelpdeskArticleSearch

RELATED_LIMIT = 3


def get_nouns(blob: TextBlob):
    try:
        return [word for word, pos in blob.pos_tags if pos[0] == "N"]
    except LookupError:
        return []


def get_noun_phrases(blob: TextBlob):
    try:
        return blob.noun_phrases
    except (LookupError, MissingCorpusError):
        return []


def search_with_enough_results(
    prev_res: list, query: str, qtype="and"
) -> tuple[list, bool]:
    out = hd_search(query, qtype=qtype)
    if not out:
        return prev_res, len(prev_res) == NUM_RESULTS
    items = prev_res + filter_public_articles(out[0].get("items", []))
    items = list({v["id"]: v for v in items}.values())[:NUM_RESULTS]  # unique results
    return items, len(items) == NUM_RESULTS


def filter_public_articles(articles: list) -> list:
    """Drop hits whose article is no longer published, the index can be stale."""
    names = {article["name"].split("#")[0] for article in articles}
    if not names:
        return []
    published = frappe.get_list(
        "HD Article",
        filters={"name": ("in", list(names)), "status": "Published"},
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
def search(query: str) -> list:
    query = sanitize_query(query)
    ret, enough = search_with_enough_results([], query)
    if enough:
        return ret
    blob = TextBlob(query)  # fallback
    if noun_phrases := get_noun_phrases(blob):
        query = " ".join(noun_phrases)
        ret, enough = search_with_enough_results(ret, query)
        if enough:
            return ret
        ret, enough = search_with_enough_results(ret, query, qtype="or")
        if enough:
            return ret
    if nouns := get_nouns(blob):
        query = " ".join(nouns)
        ret, enough = search_with_enough_results(ret, query)
        if enough:
            return ret
        ret, enough = search_with_enough_results(ret, query, qtype="or")
    return ret


@frappe.whitelist()
def get_related(query: str) -> list[dict]:
    """Published articles the reader may see that match free text, best first, as plain titles."""
    search = HelpdeskArticleSearch()
    if not search.index_exists():
        return []
    # The index filters on status and audience, so its top hits are all readable.
    return [
        {"name": row["name"], "title": strip_html_tags(row["title"])}
        for row in search.search(query)["results"][:RELATED_LIMIT]
    ]
