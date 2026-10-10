import frappe
from bs4 import BeautifulSoup
from frappe import _
from frappe.query_builder.functions import Coalesce
from frappe.rate_limiter import rate_limit
from frappe.utils import (
    cint,
    escape_html,
    expand_relative_urls,
    get_user_info_for_avatar,
)
from markdownify import markdownify

from helpdesk.helpdesk.doctype.hd_article.hd_article import (
    check_category_length,
    get_joining_values,
    get_shared_visibility,
    get_voter,
    is_readable,
    readable_filters,
    update_articles,
)
from helpdesk.search_sqlite import HelpdeskArticleSearch, reindex_articles

PUBLIC_ARTICLE_FIELDS = [
    "name",
    "title",
    "author",
    "category",
    "published_on",
    "modified",
    "views",
]
PUBLIC_CATEGORY_FIELDS = [
    "name",
    "category_name",
    "description",
    "icon",
    "pinned",
    "pinned_order",
]
# Avatars in a category page's byline.
CREATOR_LIMIT = 3
SEARCH_LIMIT = 10
SEARCH_QUERY_LENGTH = 200
# Matches the article page's reading time.
WORDS_PER_MINUTE = 200
# A category past this many articles lists only the newest.
LIST_LIMIT = 100
# The sidebar's tree and search read these in one go; past this many, the oldest are left out.
TITLES_LIMIT = 1000

VISITOR_COOKIE = "hd_visitor"
VISITOR_COOKIE_MAX_AGE = 365 * 24 * 60 * 60
VIEW_WINDOW = 60 * 60


def validate_public_access():
    """Anonymous readers only while the knowledge base is public."""
    if frappe.session.user != "Guest":
        return
    if not frappe.db.get_single_value("HD Settings", "public_knowledge_base"):
        frappe.throw(
            _("Please sign in to read the knowledge base"), frappe.PermissionError
        )


@frappe.whitelist(methods=["POST"])
def delete_articles(articles: list[str]):
    for article in articles:
        frappe.delete_doc("HD Article", article)


@frappe.whitelist(methods=["POST"])
def create_category(title: str, icon: str | None = None):
    if title.strip().lower() == "general":
        frappe.throw(
            _(
                "General is a reserved category name. Please use a different name to proceed."
            )
        )
    category = frappe.new_doc(
        "HD Article Category", category_name=title, icon=icon
    ).insert()
    article = frappe.new_doc(
        "HD Article", title="New Article", category=category.name
    ).insert()
    return {"article": article.name, "category": category.name}


def _validate_category(category: str) -> None:
    """A name, not a filter: `set_value` would take a list as one and touch every article."""
    if not isinstance(category, str) or not frappe.db.exists(
        "HD Article Category", category
    ):
        frappe.throw(_("Category not found"), frappe.DoesNotExistError)


@frappe.whitelist()
def get_category_visibility(category: str) -> str | None:
    frappe.has_permission("HD Article", "write", throw=True)
    _validate_category(category)
    return get_shared_visibility(category)


@frappe.whitelist(methods=["POST"])
def set_category_visibility(category: str, visibility: str):
    frappe.has_permission("HD Article", "write", throw=True)
    _validate_category(category)
    options = frappe.get_meta("HD Article").get_options("visibility").split("\n")
    if visibility not in options:
        frappe.throw(_("Invalid access: {0}").format(visibility))
    update_articles({"category": category}, {"visibility": visibility})


@frappe.whitelist(methods=["POST"])
def move_to_category(category: str, articles: list[str]):
    frappe.has_permission("HD Article", "write", throw=True)
    _validate_category(category)

    values = get_joining_values(category)
    for article in articles:
        check_category_length(frappe.db.get_value("HD Article", article, "category"))
        frappe.db.set_value("HD Article", article, values, update_modified=False)
    reindex_articles(articles)


@frappe.whitelist(allow_guest=True, methods=["GET"])
def get_public_articles(
    category: str | None = None, limit: int | None = None, sort: str = "latest"
) -> list[dict]:
    """Published articles the reader may see, with what a list row shows and no body."""
    validate_public_access()
    filters = readable_filters()
    if category:
        filters["category"] = category
    return frappe.get_all(
        "HD Article",
        filters=filters,
        fields=["name", "title", "excerpt"],
        order_by="views desc" if sort == "popular" else "published_on desc",
        limit_page_length=min(cint(limit) or LIST_LIMIT, LIST_LIMIT),
    )


def _get_byline(user: str) -> dict:
    """What a byline shows; never the email, which guests could harvest."""
    info = get_user_info_for_avatar(user)
    return {"name": info["name"], "image": info["image"]}


def _get_first_image(soup: BeautifulSoup) -> str | None:
    """HD Article has no cover field; the body's first image stands in for one."""
    image = soup.find("img")
    return image.get("src") if image else None


@frappe.whitelist(allow_guest=True, methods=["GET"])
def get_public_article_titles() -> list[dict]:
    """The newest articles the reader may see, as just name, title and category."""
    validate_public_access()
    return frappe.get_all(
        "HD Article",
        filters=readable_filters(),
        fields=["name", "title", "category"],
        order_by="published_on desc",
        limit_page_length=TITLES_LIMIT,
    )


@frappe.whitelist(allow_guest=True, methods=["GET"])
def get_public_article(name: str) -> dict:
    """One article, published — or any article to an agent previewing a draft."""
    name = _get_article_name(name)
    article = _get_readable_article(name, [*PUBLIC_ARTICLE_FIELDS, "content"])
    article.author = _get_byline(article.author)
    article.category_name = frappe.db.get_value(
        "HD Article Category", article.category, "category_name"
    )
    article.feedback = _get_own_feedback(name)
    article.minutes = _get_reading_minutes(
        BeautifulSoup(article.content or "", "html.parser")
    )
    return article


@frappe.whitelist(allow_guest=True, methods=["GET"])
def get_article_markdown(name: str) -> None:
    """The article as a Markdown page, to paste into an LLM or point one at."""
    article = _get_readable_article(name, ["title", "content"])
    body = markdownify(
        expand_relative_urls(article.content or ""), heading_style="ATX", bullets="-"
    )
    frappe.response.update(
        type="download",
        filename=f"{name}.md",
        filecontent=f"# {article.title}\n\n{body.strip()}\n",
        content_type="text/markdown",
        display_content_as="inline",
    )


def _get_article_name(path_name: str) -> str:
    """URLs read `<name>-<title slug>`; a name may hold hyphens too, so the longest match wins."""
    parts = path_name.split("-")
    candidates = ["-".join(parts[:i]) for i in range(len(parts), 0, -1)]
    found = set(
        frappe.get_all("HD Article", filters={"name": ["in", candidates]}, pluck="name")
    )
    return next((candidate for candidate in candidates if candidate in found), path_name)


def _get_readable_article(name: str, fields: list[str] | None = None) -> frappe._dict:
    validate_public_access()
    article = frappe.db.get_value(
        "HD Article", name, ["status", "visibility", *(fields or [])], as_dict=True
    )
    if not article or not is_readable(article):
        frappe.throw(_("Article not found"), frappe.DoesNotExistError)
    return article


@frappe.whitelist(allow_guest=True, methods=["GET"])
def get_categories(with_creators: bool = False) -> list[dict]:
    """Only those with an article the reader may see, each with `article_count`,
    and with `with_creators`, its first few authors and how many there are."""
    validate_public_access()
    counts, authors = {}, {}
    for category, author, total in frappe.get_all(
        "HD Article",
        filters=readable_filters(category=["is", "set"]),
        fields=["category", "author", {"COUNT": "*", "as": "total"}],
        group_by="category, author",
        order_by="total desc",
        as_list=True,
    ):
        counts[category] = counts.get(category, 0) + total
        authors.setdefault(category, []).append(author)
    if not counts:
        return []
    categories = frappe.get_all(
        "HD Article Category",
        filters={"name": ["in", list(counts)]},
        fields=PUBLIC_CATEGORY_FIELDS,
        order_by="category_name asc",
    )
    with_creators = cint(with_creators)
    for category in categories:
        category.article_count = counts[category.name]
        if with_creators:
            names = authors[category.name]
            category.creators = [_get_byline(name) for name in names[:CREATOR_LIMIT]]
            category.creator_count = len(names)
    return categories


@frappe.whitelist(allow_guest=True, methods=["GET"])
@rate_limit(limit=120, seconds=60)
def search_articles(query: str, limit: int = SEARCH_LIMIT) -> list[dict]:
    """Full-text matches the reader may see, best first, with `<mark>` around the hits."""
    validate_public_access()
    query = query.strip()[:SEARCH_QUERY_LENGTH]
    search = HelpdeskArticleSearch()
    if not query or not search.index_exists():
        return []
    # The index filters on status and audience, so its top hits are all readable.
    hits = search.search(query)["results"][: min(cint(limit) or SEARCH_LIMIT, SEARCH_LIMIT)]
    if not hits:
        return []
    articles = {
        article.name: article
        for article in frappe.get_all(
            "HD Article",
            filters={"name": ["in", [row["name"] for row in hits]]},
            fields=["name", "content", "category.category_name as category_name"],
        )
    }
    return [_get_search_hit(row, articles[row["name"]]) for row in hits]


def _get_search_hit(row: dict, article: frappe._dict) -> dict:
    body = BeautifulSoup(article.content or "", "html.parser")
    return {
        "name": row["name"],
        "title": escape_marked(row["title"]),
        "excerpt": escape_marked(row.get("content") or ""),
        "image": _get_first_image(body),
        "minutes": _get_reading_minutes(body),
        "category_name": article.category_name,
    }


def _get_reading_minutes(body: BeautifulSoup) -> int:
    return max(1, round(len(body.get_text().split()) / WORDS_PER_MINUTE))


def escape_marked(text: str) -> str:
    """Author text is not HTML; only the highlighter's own tags survive escaping."""
    return (
        escape_html(text)
        .replace("&lt;mark&gt;", "<mark>")
        .replace("&lt;/mark&gt;", "</mark>")
    )


@frappe.whitelist(allow_guest=True, methods=["POST"])
@rate_limit(key="article", limit=5, seconds=60 * 60)
def set_article_feedback(article: str, value: int) -> None:
    """Give feedback on a published article, signed in or not."""
    _get_readable_article(article)
    frappe.get_doc("HD Article", article).set_feedback(
        value, visitor_id=_get_visitor_id(create=True)
    )


def _get_visitor_id(create: bool = False) -> str | None:
    """A cookie that tells one `Guest` voter from another; only voting mints it."""
    if frappe.session.user != "Guest":
        return None

    key = frappe.request.cookies.get(VISITOR_COOKIE) if frappe.request else None
    if key or not create:
        return key

    key = frappe.generate_hash(length=32)
    frappe.local.cookie_manager.set_cookie(
        VISITOR_COOKIE, key, max_age=VISITOR_COOKIE_MAX_AGE, httponly=True
    )
    return key


def _get_own_feedback(article: str) -> int:
    """The caller's own feedback on an article — 0 when they have given none."""
    # A null visitor id would match every signed-in reader's row.
    if not (voter := get_voter(_get_visitor_id())):
        return 0
    feedback = frappe.db.get_value(
        "HD Article Feedback", {**voter, "article": article}, "feedback"
    )
    return cint(feedback)


@frappe.whitelist(methods=["POST"])
def merge_category(source: str, target: str):
    frappe.has_permission("HD Article Category", "delete", throw=True)

    if source == target:
        frappe.throw(_("Source and target category cannot be same"))
    _validate_category(source)
    _validate_category(target)
    if source == get_general_category():
        frappe.throw(_("Cannot merge General category"))
    update_articles({"category": source}, get_joining_values(target))
    frappe.delete_doc("HD Article Category", source)


@frappe.whitelist()
def get_general_category():
    return frappe.db.get_value(
        "HD Article Category", {"category_name": "General"}, "name"
    )


@frappe.whitelist(allow_guest=True, methods=["POST"])
@rate_limit(key="article", limit=5, seconds=VIEW_WINDOW, user_based=True)
def increment_views(article: str):
    """Count a reader once per article an hour; a re-read inside that window is no new view."""
    _get_readable_article(article)
    reader = (
        frappe.local.request_ip
        if frappe.session.user == "Guest"
        else frappe.session.user
    )
    key = f"helpdesk:article_view:{article}:{reader}"
    if frappe.cache.get_value(key):
        return
    frappe.cache.set_value(key, 1, expires_in_sec=VIEW_WINDOW)
    HDArticle = frappe.qb.DocType("HD Article")
    (
        frappe.qb.update(HDArticle)
        .set(HDArticle.views, Coalesce(HDArticle.views, 0) + 1)
        .where(HDArticle.name == article)
        .run()
    )
