import frappe
from bs4 import BeautifulSoup
from frappe import _
from frappe.rate_limiter import rate_limit
from frappe.utils import get_user_info_for_avatar

from helpdesk.utils import is_agent


def get_user_organizations():
    """Get HD Organizations the current user belongs to.

    Resolution paths:
        Path 1: user email -> Contact Email -> Contact -> HD Org Contact Item -> HD Organization
        Path 2: user email -> Contact Email -> Contact -> Dynamic Link -> HD Customer -> organization -> HD Organization

    Returns:
        None   -- agent (see all articles)
        []     -- no organization (see only Public articles)
        [str]  -- list of HD Organization names
    """
    if is_agent():
        return None

    user_email = frappe.session.user
    contacts = frappe.get_all(
        "Contact Email",
        filters={"email_id": user_email, "parenttype": "Contact"},
        pluck="parent",
    )
    if not contacts:
        return []

    orgs = set()

    # Path 1: Contact -> HD Organization (via contacts child table)
    direct_orgs = frappe.get_all(
        "HD Organization",
        filters=[["HD Organization Contact Item", "contact", "in", contacts]],
        pluck="name",
    )
    orgs.update(direct_orgs)

    # Path 2: Contact -> HD Customer -> HD Organization
    customers = frappe.get_all(
        "Dynamic Link",
        filters={
            "parenttype": "Contact",
            "parent": ["in", contacts],
            "link_doctype": "HD Customer",
        },
        pluck="link_name",
    )
    if customers:
        customer_orgs = frappe.get_all(
            "HD Customer",
            filters={"name": ["in", customers], "organization": ["is", "set"]},
            pluck="organization",
        )
        orgs.update(customer_orgs)

    return list(orgs)


def is_article_visible(article_name, user_orgs):
    """Check if an article is visible to the current user.

    Args:
        article_name: HD Article name
        user_orgs: result from get_user_organizations()
    """
    if user_orgs is None:
        return True

    visibility = frappe.db.get_value("HD Article", article_name, "visibility")
    if visibility != "Restricted":
        return True

    if not user_orgs:
        return False

    allowed_orgs = frappe.get_all(
        "HD Article Organization",
        filters={"parent": article_name, "parenttype": "HD Article"},
        pluck="organization",
    )
    return bool(set(user_orgs) & set(allowed_orgs))


@frappe.whitelist(allow_guest=True)
def get_article(name: str):
    article = frappe.get_doc("HD Article", name).as_dict()

    user_orgs = get_user_organizations()

    # user_orgs is None for agents -- they see everything
    if user_orgs is not None and article["status"] != "Published":
        frappe.throw(_("Access denied"), frappe.PermissionError)

    if not is_article_visible(name, user_orgs):
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
        article_category = frappe.db.get_value("HD Article", article, "category")
        if not article_category:
            frappe.throw(_("Article {0} not found").format(article))
        category_existing_articles = frappe.db.count(
            "HD Article", {"category": article_category}
        )
        if category_existing_articles == 1:
            frappe.throw(_("Category must have at least one article"))
        frappe.db.set_value(
            "HD Article", article, "category", category, update_modified=False
        )


@frappe.whitelist()
def get_categories():
    categories = frappe.get_all(
        "HD Article Category",
        fields=["name", "category_name", "modified"],
    )
    user_orgs = get_user_organizations()

    for c in categories:
        if user_orgs is None:
            # Agent: count all published articles
            c["article_count"] = frappe.db.count(
                "HD Article", filters={"category": c.name, "status": "Published"}
            )
        else:
            # Non-agent: count only visible articles
            public_count = frappe.db.count(
                "HD Article",
                filters={"category": c.name, "status": "Published", "visibility": ["in", ["Public", ""]]},
            )
            if not user_orgs:
                c["article_count"] = public_count
            else:
                restricted_count = frappe.db.sql("""
                    SELECT COUNT(DISTINCT a.name)
                    FROM `tabHD Article` a
                    INNER JOIN `tabHD Article Organization` ao
                        ON ao.parent = a.name AND ao.parenttype = 'HD Article'
                    WHERE a.category = %s
                        AND a.status = 'Published'
                        AND a.visibility = 'Restricted'
                        AND ao.organization IN %s
                """, (c.name, user_orgs))[0][0]
                c["article_count"] = public_count + restricted_count

    categories.sort(key=lambda c: c["article_count"], reverse=True)
    categories = [c for c in categories if c["article_count"] > 0]
    return categories


@frappe.whitelist()
def get_category_articles(category: str):
    user_orgs = get_user_organizations()

    if user_orgs is None:
        # Agent: all published articles
        articles = frappe.get_all(
            "HD Article",
            filters={"category": category, "status": "Published"},
            fields=["name", "title", "published_on", "modified", "author", "content"],
        )
    else:
        # Non-agent: Public + visible Restricted articles
        articles = frappe.get_all(
            "HD Article",
            filters={
                "category": category,
                "status": "Published",
                "visibility": ["in", ["Public", ""]],
            },
            fields=["name", "title", "published_on", "modified", "author", "content"],
        )
        if user_orgs:
            restricted = frappe.db.sql("""
                SELECT DISTINCT a.name, a.title, a.published_on, a.modified, a.author, a.content
                FROM `tabHD Article` a
                INNER JOIN `tabHD Article Organization` ao
                    ON ao.parent = a.name AND ao.parenttype = 'HD Article'
                WHERE a.category = %s
                    AND a.status = 'Published'
                    AND a.visibility = 'Restricted'
                    AND ao.organization IN %s
            """, (category, user_orgs), as_dict=True)
            articles.extend(restricted)

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


@frappe.whitelist()
@rate_limit(key="article", seconds=60 * 60)
def increment_views(article: str):
    views = frappe.db.get_value("HD Article", article, "views") or 0
    views += 1
    frappe.db.set_value("HD Article", article, "views", views, update_modified=False)
