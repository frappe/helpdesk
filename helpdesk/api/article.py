import frappe
from textblob import TextBlob
from textblob.exceptions import MissingCorpusError

from helpdesk.search import NUM_RESULTS
from helpdesk.search import search as hd_search


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


def search_with_enough_results(prev_res: list, query: str) -> tuple[list, bool]:
    out = hd_search(query, only_articles=True)
    if not out:
        return prev_res, len(prev_res) == NUM_RESULTS
    items = prev_res + out[0].get("items", [])
    items = list({v["id"]: v for v in items}.values())[:NUM_RESULTS]  # unique results
    return items, len(items) == NUM_RESULTS


@frappe.whitelist()
def search(query: str) -> list:
    query = query.strip().lower()
    ret, enough = search_with_enough_results([], query)
    if enough:
        return ret
    blob = TextBlob(query)  # fallback
    if noun_phrases := get_noun_phrases(blob):
        and_query = " ".join(noun_phrases)
        ret, enough = search_with_enough_results(ret, and_query)
        if enough:
            return ret
        or_query = "|".join(noun_phrases)
        ret, enough = search_with_enough_results(ret, or_query)
        if enough:
            return ret
    if nouns := get_nouns(blob):
        and_query = " ".join(nouns)
        ret, enough = search_with_enough_results(ret, and_query)
        if enough:
            return ret
        or_query = "|".join(nouns)
        ret, enough = search_with_enough_results(ret, or_query)
    return ret
