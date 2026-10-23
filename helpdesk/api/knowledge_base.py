import frappe
from bs4 import BeautifulSoup
from frappe import _
from frappe.core.utils import html2text
from frappe.query_builder.functions import Coalesce
from frappe.rate_limiter import rate_limit
from frappe.utils import (
    cint,
    escape_html,
    expand_relative_urls,
    get_user_info_for_avatar,
)
from frappe.website.utils import cleanup_page_name, find_first_image

from helpdesk.api.article import search_accessible_articles
from helpdesk.helpdesk.doctype.hd_article.hd_article import (
    can_view_article,
    get_voter,
    make_article_filters,
)
from helpdesk.helpdesk.doctype.hd_article_category import hd_article_category
from helpdesk.helpdesk.doctype.hd_article_category.hd_article_category import (
    get_stricter_visibility,
    move_category_articles,
)
from helpdesk.search import NUM_RESULTS

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
SEARCH_LIMIT = NUM_RESULTS
SEARCH_QUERY_LENGTH = 200
WORDS_PER_MINUTE = 200
LIST_LIMIT = 100
# the sidebar reads its titles in one request; newer ones win past this
TITLES_LIMIT = 1000

VISITOR_COOKIE = "hd_visitor"
VISITOR_COOKIE_MAX_AGE = 365 * 24 * 60 * 60
VIEW_WINDOW = 60 * 60


def validate_public_access():
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
    """A list would act as a filter and touch every article."""
    if not isinstance(category, str) or not frappe.db.exists(
        "HD Article Category", category
    ):
        frappe.throw(_("Category not found"), frappe.DoesNotExistError)


@frappe.whitelist()
def get_category_visibility(category: str) -> str | None:
    frappe.has_permission("HD Article", "write", throw=True)
    _validate_category(category)
    return hd_article_category.get_category_visibility(category)


@frappe.whitelist(methods=["POST"])
def set_category_visibility(category: str, visibility: str):
    frappe.has_permission("HD Article", "write", throw=True)
    _validate_category(category)
    options = frappe.get_meta("HD Article").get_options("visibility").split("\n")
    if visibility not in options:
        frappe.throw(_("Invalid access: {0}").format(visibility))
    # saved one by one for version history
    for name in frappe.get_all(
        "HD Article",
        filters={"category": category, "visibility": ["!=", visibility]},
        pluck="name",
    ):
        article = frappe.get_doc("HD Article", name)
        article.visibility = visibility
        article.save()


@frappe.whitelist(methods=["POST"])
def move_to_category(category: str, articles: list[str]):
    frappe.has_permission("HD Article", "write", throw=True)
    _validate_category(category)

    # read before the move changes it
    category_visibility = hd_article_category.get_category_visibility(category)
    for name in articles:
        article = frappe.get_doc("HD Article", name)
        article.category = category
        article.visibility = get_stricter_visibility(
            article.visibility, category_visibility
        )
        article.save()


# Guest endpoints: make_article_filters limits guests to Public articles.
@frappe.whitelist(allow_guest=True, methods=["GET"])  # nosemgrep
def get_articles(
    category: str | None = None, limit: int | None = None, sort: str = "latest"
) -> list[dict]:
    validate_public_access()
    filters = make_article_filters()
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
    """Never the email: guests could harvest it. Never a private image: readers get a 403."""
    info = get_user_info_for_avatar(user)
    image = info["image"]
    if image and image.startswith("/private/"):
        image = None
    return {"name": info["name"], "image": image}


@frappe.whitelist(allow_guest=True, methods=["GET"])  # nosemgrep
# guests count per IP, so leave room for a shared office address
@rate_limit(limit=120, seconds=60, user_based=True)
def get_kb_sidebar() -> list[dict]:
    validate_public_access()
    articles = {}
    for row in frappe.get_all(
        "HD Article",
        filters=make_article_filters(category=["is", "set"]),
        fields=["name", "title", "category"],
        order_by="published_on desc",
        limit_page_length=TITLES_LIMIT,
    ):
        articles.setdefault(row.pop("category"), []).append(row)
    categories = _get_categories(with_creators=True)
    for category in categories:
        category.articles = articles.get(category.name, [])
    return categories


@frappe.whitelist(allow_guest=True, methods=["GET"])  # nosemgrep
def get_article(name: str) -> dict:
    name = _get_article_name(name)
    article = _get_viewable_article(name, [*PUBLIC_ARTICLE_FIELDS, "content"])
    article.author = _get_byline(article.author)
    article.title_slug = cleanup_page_name(article.title)
    article.category_name = frappe.db.get_value(
        "HD Article Category", article.category, "category_name"
    )
    article.feedback = _get_own_feedback(name)
    article.minutes = _get_reading_minutes(
        BeautifulSoup(article.content or "", "html.parser")
    )
    return article


@frappe.whitelist(allow_guest=True, methods=["GET"])  # nosemgrep
def get_article_markdown(name: str) -> None:
    article = _get_viewable_article(name, ["title", "content"])
    body = html2text(expand_relative_urls(article.content or ""), wrap=False)
    frappe.response.update(
        type="download",
        filename=f"{name}.md",
        filecontent=f"# {article.title}\n\n{body.strip()}\n",
        content_type="text/markdown",
        display_content_as="inline",
    )


def _get_article_name(path_name: str) -> str:
    """Names are hashes without hyphens; URLs append `-<title slug>`."""
    return path_name.split("-", 1)[0]


def _get_viewable_article(name: str, fields: list[str] | None = None) -> frappe._dict:
    validate_public_access()
    article = frappe.db.get_value(
        "HD Article", name, ["status", "visibility", *(fields or [])], as_dict=True
    )
    if not article or not can_view_article(frappe.session.user, article):
        frappe.throw(_("Article not found"), frappe.DoesNotExistError)
    return article


@frappe.whitelist(allow_guest=True, methods=["GET"])  # nosemgrep
def get_categories() -> list[dict]:
    validate_public_access()
    return _get_categories()


def _get_categories(with_creators: bool = False) -> list[dict]:
    counts, authors = {}, {}
    for category, author, total in frappe.get_all(
        "HD Article",
        filters=make_article_filters(category=["is", "set"]),
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
    for category in categories:
        category.article_count = counts[category.name]
        if with_creators:
            category.creators = [_get_byline(name) for name in authors[category.name]]
    return categories


@frappe.whitelist(allow_guest=True, methods=["GET"])  # nosemgrep
@rate_limit(limit=120, seconds=60, user_based=True)
def search_articles(query: str, limit: int = SEARCH_LIMIT) -> list[dict]:
    validate_public_access()
    query = query.strip()[:SEARCH_QUERY_LENGTH]
    if not query:
        return []
    hits = search_accessible_articles(query)[
        : min(cint(limit) or SEARCH_LIMIT, SEARCH_LIMIT)
    ]
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
    return [
        _get_search_hit(row, articles[row["name"]])
        for row in hits
        if row["name"] in articles
    ]


def _get_search_hit(row: dict, article: frappe._dict) -> dict:
    content = article.content or ""
    return {
        "name": row["name"],
        "title": escape_marked(row["title"]),
        "title_slug": row["title_slug"],
        "excerpt": escape_marked(row["excerpt"]),
        # no cover field; the first body image stands in
        "image": find_first_image(content),
        "minutes": _get_reading_minutes(BeautifulSoup(content, "html.parser")),
        "category_name": article.category_name,
    }


def _get_reading_minutes(body: BeautifulSoup) -> int:
    return max(1, round(len(body.get_text().split()) / WORDS_PER_MINUTE))


def escape_marked(text: str) -> str:
    """Only the highlighter's own tags survive escaping."""
    return (
        escape_html(text)
        .replace("&lt;mark&gt;", "<mark>")
        .replace("&lt;/mark&gt;", "</mark>")
    )


@frappe.whitelist(allow_guest=True, methods=["POST"])  # nosemgrep
@rate_limit(key="article", limit=5, seconds=60 * 60, user_based=True)
def vote_on_article(article: str, vote: int) -> None:
    """0 withdraws, 1 helpful, 2 not helpful."""
    _get_viewable_article(article)
    frappe.get_doc("HD Article", article).set_feedback(
        vote, visitor_id=_get_visitor_id(create=True)
    )


def _get_visitor_id(create: bool = False) -> str | None:
    """Tells one Guest voter from another; only voting mints it."""
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
    move_category_articles(source, target)
    frappe.delete_doc("HD Article Category", source)


@frappe.whitelist()
def get_general_category():
    return frappe.db.get_value(
        "HD Article Category", {"category_name": "General"}, "name"
    )


@frappe.whitelist(allow_guest=True, methods=["POST"])  # nosemgrep
def increment_views(article: str):
    # an agent previewing a draft
    if _get_viewable_article(article).status != "Published":
        return
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
