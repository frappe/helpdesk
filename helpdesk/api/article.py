import frappe
from textblob import TextBlob

from helpdesk.search import search as hd_search


def get_nouns(blob: TextBlob):
    try:
        return [word for word, pos in blob.pos_tags if pos[0] == "N"]
    except LookupError:
        return []


def get_noun_phrases(blob: TextBlob):
    try:
        return blob.noun_phrases
    except LookupError:
        return []


@frappe.whitelist()
def search(query: str):
    out = hd_search(query, only_articles=True)
    if not out:  # fallback
        blob = TextBlob(query)
        if noun_phrases := get_noun_phrases(blob):
            and_query = " ".join(noun_phrases)
            or_query = "|".join(noun_phrases)
            out = hd_search(and_query, only_articles=True) or hd_search(
                or_query, only_articles=True
            )
        if not out and (nouns := get_nouns(blob)):
            and_query = " ".join(nouns)
            or_query = "|".join(nouns)
            out = hd_search(and_query, only_articles=True) or hd_search(
                or_query, only_articles=True
            )
        if not out:
            return []
    return out[0].get("items", [])
