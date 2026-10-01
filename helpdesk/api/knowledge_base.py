import frappe
from bs4 import BeautifulSoup
from frappe import _
from frappe.rate_limiter import rate_limit
from frappe.utils import escape_html, get_user_info_for_avatar

from helpdesk.search_sqlite import HelpdeskArticleSearch
from helpdesk.utils import is_agent

# Who a published article is written for, widest first. `Public` is the knowledge base as
# it has always been; the other two are gates behind `Published`.
PUBLIC = "Public"
CUSTOMERS_ONLY = "Customers only"
AGENTS_ONLY = "Agents only"


def validate_public_access():
    """Anonymous readers only while the knowledge base is public.

    The portal sends a signed-out visitor to the login page before it asks for
    anything, but that is a courtesy — this is the boundary.
    """
    if frappe.session.user != "Guest":
        return
    if not frappe.db.get_single_value("HD Settings", "public_knowledge_base"):
        frappe.throw(
            _("Please sign in to read the knowledge base"), frappe.PermissionError
        )


def readable_audiences() -> list[str] | None:
    """Which audiences the caller belongs to — `None` where every one of them is theirs.

    An agent reads the whole knowledge base. Everyone else is held to what was written
    for them: a signed-in customer to the public and customer articles, and an anonymous
    reader to the public ones alone.
    """
    if is_agent():
        return None
    if frappe.session.user == "Guest":
        return [PUBLIC]
    return [PUBLIC, CUSTOMERS_ONLY]


def readable_filters(**extra) -> dict:
    """What a reader is allowed to see, as filters.

    Published, always — plus the audiences that are theirs, so an article written for
    someone else stays out of their lists, out of the popular-category tallies, and out
    of search.
    """
    filters = {"status": "Published", **extra}
    audiences = readable_audiences()
    if audiences is not None:
        filters["visibility"] = ["in", audiences]
    return filters


def is_readable(article) -> bool:
    """The same rule for one article already fetched."""
    if is_agent():
        return True
    if article.get("status") != "Published":
        return False
    return article.get("visibility") in readable_audiences()


@frappe.whitelist(allow_guest=True)
def get_article(name: str):
    validate_public_access()
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

    return article


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


@frappe.whitelist()
def get_categories():
    categories = frappe.get_list(
        "HD Article Category",
        fields=["name", "category_name", "modified"],
    )
    for c in categories:
        c["article_count"] = frappe.db.count(
            "HD Article", filters=readable_filters(category=c.name)
        )

    categories.sort(key=lambda c: c["article_count"], reverse=True)
    categories = [c for c in categories if c["article_count"] > 0]
    return categories


# The public knowledge base reads through the endpoints below rather than
# `frappe.client.get_list`/`get`, which frappe does not open to guests. The field
# lists are fixed and the status filter is not a parameter, so an anonymous caller
# can widen neither.
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
PUBLIC_CATEGORY_FIELDS = ["name", "category_name", "description", "icon"]
EXCERPT_LENGTH = 140
SEARCH_LIMIT = 10

VISITOR_COOKIE = "hd_visitor"
VISITOR_COOKIE_MAX_AGE = 365 * 24 * 60 * 60
VIEW_WINDOW = 60 * 60


@frappe.whitelist(allow_guest=True, methods=["GET"])
def get_popular_categories(limit: int = 3) -> list[dict]:
    """Categories drawing the most article views, most-viewed first; none with zero views."""
    validate_public_access()
    ranked = frappe.get_all(
        "HD Article",
        filters={**readable_filters(), "category": ["is", "set"], "views": [">", 0]},
        fields=["category", {"SUM": "views", "as": "total"}],
        group_by="category",
        order_by="total desc",
        limit_page_length=int(limit),
    )
    labels = dict(
        frappe.get_all(
            "HD Article Category",
            filters={"name": ["in", [row.category for row in ranked]]},
            fields=["name", "category_name"],
            as_list=True,
        )
    )
    return [
        {"name": row.category, "label": labels.get(row.category) or row.category}
        for row in ranked
    ]


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
        fields=[*PUBLIC_ARTICLE_FIELDS, "content"],
        order_by="views desc" if sort == "popular" else "published_on desc",
        limit_page_length=int(limit) if limit else 0,
    )
    for article in articles:
        soup = BeautifulSoup(article.pop("content") or "", "html.parser")
        article.excerpt = soup.get_text(" ", strip=True)[:EXCERPT_LENGTH]
        article.image = first_image(soup)
        article.author = get_user_info_for_avatar(article.author)
    return articles


def first_image(soup: BeautifulSoup) -> str | None:
    """HD Article has no cover field; the body's first image stands in for one."""
    image = soup.find("img")
    return image.get("src") if image else None


@frappe.whitelist(allow_guest=True, methods=["GET"])
def get_public_article(name: str) -> dict:
    """One article, published — or any article to an agent previewing a draft."""
    validate_public_access()
    article = frappe.db.get_value(
        "HD Article", name, [*PUBLIC_ARTICLE_FIELDS, "content"], as_dict=True
    )
    if not article or not is_readable(article):
        frappe.throw(_("Article not found"), frappe.DoesNotExistError)
    article.author = get_user_info_for_avatar(article.author)
    article.category_name = frappe.db.get_value(
        "HD Article Category", article.category, "category_name"
    )
    # The reader's own vote rides along, so the page can show it filled in without
    # a second call. Named as `get_article` names it.
    article.feedback = get_own_vote(name)
    return article


@frappe.whitelist(allow_guest=True, methods=["GET"])
def get_public_categories(limit: int | None = None) -> list[dict]:
    validate_public_access()
    return frappe.get_all(
        "HD Article Category",
        fields=PUBLIC_CATEGORY_FIELDS,
        order_by="category_name asc",
        limit_page_length=int(limit) if limit else 0,
    )


@frappe.whitelist(allow_guest=True, methods=["GET"])
def get_public_category(name: str) -> dict:
    validate_public_access()
    category = frappe.db.get_value(
        "HD Article Category", name, PUBLIC_CATEGORY_FIELDS, as_dict=True
    )
    if not category:
        frappe.throw(_("Category not found"), frappe.DoesNotExistError)
    return category


@frappe.whitelist(allow_guest=True, methods=["GET"])
def search_articles(query: str, limit: int = SEARCH_LIMIT) -> list[dict]:
    """Full-text matches the reader may see, best first, with `<mark>` around the hits.

    Empty until the index exists; frappe builds it in the background after migrate.
    """
    validate_public_access()
    search = HelpdeskArticleSearch()
    if not query.strip() or not search.index_exists():
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
    labels = dict(
        frappe.get_all(
            "HD Article Category",
            filters={"name": ["in", [a.category for a in readable.values()]]},
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
        for row in results
        if row["name"] in readable
    ][: int(limit)]


def escape_marked(text: str) -> str:
    """Author text is not HTML; only the highlighter's own tags survive escaping."""
    return (
        escape_html(text)
        .replace("&lt;mark&gt;", "<mark>")
        .replace("&lt;/mark&gt;", "</mark>")
    )


@frappe.whitelist(allow_guest=True, methods=["POST"])
@rate_limit(key="article", limit=5, seconds=60 * 60)
def vote_on_article(article: str, value: int) -> dict:
    """Vote on a published article, signed in or not.

    Not `HD Article.set_feedback` over `run_doc_method`: a signed-out reader holds no
    read permission on the doctype, which is why every public read here is an
    allow-listed endpoint too.
    """
    validate_public_access()
    doc = frappe.get_doc("HD Article", article)
    if not is_readable(doc):
        frappe.throw(_("Article not found"), frappe.DoesNotExistError)

    doc.set_feedback(int(value), visitor_id=get_visitor_id(create=True))
    return get_article_votes(article)


def get_visitor_id(create: bool = False) -> str | None:
    """Tell one signed-out reader from another.

    Frappe answers every anonymous request as the same `Guest` user, so without this
    all their votes would land on one row. Reading never mints a cookie: only voting does.
    """
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
        # No cookie yet, so no vote. Filtering on a null visitor would otherwise
        # match every signed-in reader's row.
        return "0"

    vote = frappe.db.get_value(
        "HD Article Feedback", {**voter, "article": article}, "feedback"
    )
    return str(vote or "0")


def get_article_votes(article: str) -> dict:
    # `get_all` rather than `db.count`: the latter checks read permission, which a
    # signed-out voter does not have on this doctype.
    votes = [
        str(vote)
        for vote in frappe.get_all(
            "HD Article Feedback", filters={"article": article}, pluck="feedback"
        )
    ]
    return {"likes": votes.count("1"), "dislikes": votes.count("2")}


@frappe.whitelist()
def get_category_articles(category: str):
    articles = frappe.get_list(
        "HD Article",
        filters=readable_filters(category=category),
        fields=["name", "title", "published_on", "modified", "author", "content"],
    )
    for article in articles:
        article["author"] = get_user_info_for_avatar(article["author"])
        soup = BeautifulSoup(article["content"], "html.parser")
        article["content"] = str(soup.text)[:100]

    return articles


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


@frappe.whitelist()
def get_category_title(category: str):
    return frappe.db.get_value("HD Article Category", category, "category_name")


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
    views = frappe.db.get_value("HD Article", article, "views") or 0
    frappe.db.set_value(
        "HD Article", article, "views", views + 1, update_modified=False
    )
