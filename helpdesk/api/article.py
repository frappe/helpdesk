import frappe
from textblob import TextBlob
from textblob.exceptions import MissingCorpusError

from helpdesk.search import NUM_RESULTS
from helpdesk.search import search as hd_search
from helpdesk.search_i18n import contains_cjk, normalize_search_text


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
    items = prev_res + out[0].get("items", [])
    items = list({v["id"]: v for v in items}.values())[:NUM_RESULTS]  # unique results
    return items, len(items) == NUM_RESULTS


def sanitize_query(query: str) -> str:
    return normalize_search_text(query)


@frappe.whitelist()
def get_article_stats(article_name: str):
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
    if not query:
        return []
    ret, enough = search_with_enough_results([], query)
    if enough or contains_cjk(query):
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
