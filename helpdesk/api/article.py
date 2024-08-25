import frappe
from textblob import TextBlob

from helpdesk.search import search as hd_search


def get_nouns(text: str):
    blob = TextBlob(text)
    try:
        return [word for word, pos in blob.pos_tags if pos[0] == "N"]
    except LookupError:
        return []


@frappe.whitelist()
def search(query: str):
    out = hd_search(query, only_articles=True)
    if not out:  # fallback
        if nouns := get_nouns(query):
            query = " ".join(nouns)
            out = hd_search(query, only_articles=True)
        if not out:
            return []
    return out[0].get("items", [])
