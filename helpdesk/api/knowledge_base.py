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

from helpdesk.search_sqlite import HelpdeskArticleSearch
from helpdesk.utils import is_agent

PUBLIC = "Public"
CUSTOMERS_ONLY = "Customers only"


def validate_public_access():
    """Anonymous readers only while the knowledge base is public."""
    if frappe.session.user != "Guest":
        return
    if not frappe.db.get_single_value("HD Settings", "public_knowledge_base"):
        frappe.throw(
            _("Please sign in to read the knowledge base"), frappe.PermissionError
        )


def readable_audiences(user: str | None = None) -> list[str] | None:
    """The audiences `user` may read; `None` for an agent, who reads them all."""
    user = user or frappe.session.user
    if is_agent(user):
        return None
    if user == "Guest":
        return [PUBLIC]
    return [PUBLIC, CUSTOMERS_ONLY]


def readable_filters(**extra) -> dict:
    """Published articles in the caller's audiences, as filters."""
    filters = {"status": "Published", **extra}
    audiences = readable_audiences()
    if audiences is not None:
        filters["visibility"] = ["in", audiences]
    return filters


def is_readable(article, user: str | None = None) -> bool:
    """The same rule for one article already fetched."""
    audiences = readable_audiences(user)
    if audiences is None:
        return True
    return (
        article.get("status") == "Published" and article.get("visibility") in audiences
    )


@frappe.whitelist()
def get_article(name: str):
    article = frappe.get_doc("HD Article", name).as_dict()

    if not is_readable(article):
        frappe.throw(_("Access denied"), frappe.PermissionError)

    author = get_user_info_for_avatar(article["author"])
    feedback = (
        frappe.db.get_value(
            "HD Article Feedback",
            {"article": name, "user": frappe.session.user},
            "feedback",
        )
        or 0
    )

    return {
        "name": article.name,
        "title": article.title,
        "content": article.content,
        "author": author,
        "creation": article.creation,
        "status": article.status,
        "published_on": article.published_on,
        "modified": article.modified,
        "category_name": frappe.db.get_value(
            "HD Article Category", article.category, "category_name"
        ),
        "category_id": article.category,
        "visibility": article.visibility,
        "feedback": int(feedback),
    }


@frappe.whitelist()
def delete_articles(articles: list[str]):
    for article in articles:
        frappe.delete_doc("HD Article", article)


@frappe.whitelist()
def create_category(title: str):
    if title.strip().lower() == "general":
        frappe.throw(
            _(
                "General is a reserved category name. Please use a different name to proceed."
            )
        )
    category = frappe.new_doc("HD Article Category", category_name=title).insert()
    article = frappe.new_doc(
        "HD Article", title="New Article", category=category.name
    ).insert()
    return {"article": article.name, "category": category.name}


@frappe.whitelist()
def move_to_category(category: str, articles: list[str]):
    frappe.has_permission("HD Article", "write", throw=True)

    for article in articles:
        try:
            article_category = frappe.db.get_value("HD Article", article, "category")
            category_existing_articles = frappe.db.count(
                "HD Article", {"category": article_category}
            )
            if category_existing_articles == 1:
                frappe.throw(_("Category must have atleast one article"))
                return
            else:
                frappe.db.set_value(
                    "HD Article", article, "category", category, update_modified=False
                )
        except Exception as e:
            frappe.db.rollback()
            frappe.throw(_("Error moving article to category"))


# Fixed fields and no status parameter: guests read through these, so they cannot widen them.
PUBLIC_ARTICLE_FIELDS = [
    "name",
    "title",
    "author",
    "category",
    "status",
    "visibility",
    "published_on",
    "modified",
    "views",
]
PUBLIC_CATEGORY_FIELDS = ["name", "category_name", "description", "icon", "pinned"]
EXCERPT_LENGTH = 140
SEARCH_LIMIT = 10
SEARCH_QUERY_LENGTH = 200
# A category past this many articles lists only the newest.
LIST_LIMIT = 100

VISITOR_COOKIE = "hd_visitor"
VISITOR_COOKIE_MAX_AGE = 365 * 24 * 60 * 60
VIEW_WINDOW = 60 * 60


@frappe.whitelist(allow_guest=True, methods=["GET"])
def get_public_articles(
    category: str | None = None, limit: int | None = None, sort: str = "latest"
) -> list[dict]:
    """Published articles the reader may see, with what a list row shows and no body."""
    validate_public_access()
    filters = readable_filters()
    if category:
        filters["category"] = category
    articles = frappe.get_all(
        "HD Article",
        filters=filters,
        fields=["name", "title", "content"],
        order_by="views desc" if sort == "popular" else "published_on desc",
        limit_page_length=min(cint(limit) or LIST_LIMIT, LIST_LIMIT),
    )
    for article in articles:
        article.excerpt = excerpt(
            BeautifulSoup(article.pop("content") or "", "html.parser")
        )
    return articles


def byline(user: str) -> dict:
    """What a byline shows; never the email, which guests could harvest."""
    info = get_user_info_for_avatar(user)
    return {"name": info["name"], "image": info["image"]}


def excerpt(soup: BeautifulSoup) -> str:
    """The first paragraph, read as a sentence: headings and table cells would run into it."""
    paragraph = next((p for p in soup.find_all("p") if p.get_text(strip=True)), soup)
    return " ".join(paragraph.get_text().split())[:EXCERPT_LENGTH]


def first_image(soup: BeautifulSoup) -> str | None:
    """HD Article has no cover field; the body's first image stands in for one."""
    image = soup.find("img")
    return image.get("src") if image else None


@frappe.whitelist(allow_guest=True, methods=["GET"])
def get_public_article_titles() -> list[dict]:
    """Every article the reader may see, as just its name, title and category."""
    validate_public_access()
    return frappe.get_all(
        "HD Article",
        filters=readable_filters(),
        fields=["name", "title", "category"],
        order_by="published_on desc",
    )


@frappe.whitelist(allow_guest=True, methods=["GET"])
def get_public_article(name: str) -> dict:
    """One article, published — or any article to an agent previewing a draft."""
    article = get_readable_article(name, [*PUBLIC_ARTICLE_FIELDS, "content"])
    article.author = byline(article.author)
    article.category_name = frappe.db.get_value(
        "HD Article Category", article.category, "category_name"
    )
    article.feedback = get_own_vote(name)
    return article


@frappe.whitelist(allow_guest=True, methods=["GET"])
def get_article_markdown(name: str) -> None:
    """The article as a Markdown page, to paste into an LLM or point one at."""
    article = get_readable_article(name, ["title", "content", "status", "visibility"])
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


def get_readable_article(name: str, fields: list[str]) -> frappe._dict:
    """`fields` must carry `status` and `visibility`: they decide who may read it."""
    validate_public_access()
    article = frappe.db.get_value("HD Article", name, fields, as_dict=True)
    if not article or not is_readable(article):
        frappe.throw(_("Article not found"), frappe.DoesNotExistError)
    return article


@frappe.whitelist(allow_guest=True, methods=["GET"])
def get_categories() -> list[dict]:
    """Only those with an article the reader may see, each with `article_count`."""
    validate_public_access()
    counts = readable_article_counts()
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
    return categories


def readable_article_counts() -> dict[str, int]:
    return dict(
        frappe.get_all(
            "HD Article",
            filters=readable_filters(category=["is", "set"]),
            fields=["category", {"COUNT": "*", "as": "total"}],
            group_by="category",
            as_list=True,
        )
    )


@frappe.whitelist(allow_guest=True, methods=["GET"])
@rate_limit(limit=120, seconds=60)
def search_articles(query: str, limit: int = SEARCH_LIMIT) -> list[dict]:
    """Full-text matches the reader may see, best first, with `<mark>` around the hits."""
    validate_public_access()
    query = query.strip()[:SEARCH_QUERY_LENGTH]
    search = HelpdeskArticleSearch()
    if not query or not search.index_exists():
        return []
    results = search.search(query)["results"]
    if not results:
        return []
    # The index knows status, not audience, so the audience gate is one bounded query.
    readable = {
        article.name: article
        for article in frappe.get_all(
            "HD Article",
            filters=readable_filters(name=["in", [row["name"] for row in results]]),
            fields=["name", "content", "category"],
        )
    }
    hits = [row for row in results if row["name"] in readable][: cint(limit)]
    labels = dict(
        frappe.get_all(
            "HD Article Category",
            filters={"name": ["in", [readable[row["name"]].category for row in hits]]},
            fields=["name", "category_name"],
            as_list=True,
        )
    )
    return [
        {
            "name": row["name"],
            "title": escape_marked(row["title"]),
            "excerpt": escape_marked(row.get("content") or ""),
            "image": first_image(
                BeautifulSoup(readable[row["name"]].content or "", "html.parser")
            ),
            "category_name": labels.get(readable[row["name"]].category),
        }
        for row in hits
    ]


def escape_marked(text: str) -> str:
    """Author text is not HTML; only the highlighter's own tags survive escaping."""
    return (
        escape_html(text)
        .replace("&lt;mark&gt;", "<mark>")
        .replace("&lt;/mark&gt;", "</mark>")
    )


@frappe.whitelist(allow_guest=True, methods=["POST"])
@rate_limit(key="article", limit=5, seconds=60 * 60)
def vote_on_article(article: str, value: int) -> None:
    """Vote on a published article, signed in or not."""
    validate_public_access()
    doc = frappe.get_doc("HD Article", article)
    if not is_readable(doc):
        frappe.throw(_("Article not found"), frappe.DoesNotExistError)

    doc.set_feedback(cint(value), visitor_id=get_visitor_id(create=True))


def get_visitor_id(create: bool = False) -> str | None:
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


def get_own_vote(article: str) -> str:
    """The caller's own vote on an article — "0" when they have not cast one."""
    if frappe.session.user != "Guest":
        voter = {"user": frappe.session.user}
    elif visitor_id := get_visitor_id():
        voter = {"visitor_id": visitor_id}
    else:
        # A null visitor id would match every signed-in reader's row.
        return "0"

    vote = frappe.db.get_value(
        "HD Article Feedback", {**voter, "article": article}, "feedback"
    )
    return str(vote or "0")


@frappe.whitelist()
def merge_category(source: str, target: str):
    frappe.has_permission("HD Article Category", "delete", throw=True)

    if source == target:
        frappe.throw(_("Source and target category cannot be same"))
    general_category = get_general_category()
    if source == general_category:
        frappe.throw(_("Cannot merge General category"))
    source_articles = frappe.get_all(
        "HD Article",
        filters={"category": source},
        pluck="name",
    )
    for article in source_articles:
        frappe.db.set_value(
            "HD Article", article, "category", target, update_modified=False
        )

    frappe.delete_doc("HD Article Category", source)


@frappe.whitelist()
def get_general_category():
    return frappe.db.get_value(
        "HD Article Category", {"category_name": "General"}, "name"
    )


@frappe.whitelist(allow_guest=True, methods=["POST"])
def increment_views(article: str):
    """Count a reader once per article an hour; a re-read inside that window is no new view."""
    validate_public_access()
    row = frappe.db.get_value(
        "HD Article", article, ["status", "visibility"], as_dict=True
    )
    if not row or not is_readable(row):
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
