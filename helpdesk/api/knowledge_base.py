from contextlib import suppress

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
    MAX_PINNED_ARTICLES,
    PRIVATE,
    can_view_article,
    get_voter,
    make_article_filters,
    throw_pin_limit,
)
from helpdesk.helpdesk.doctype.hd_article_category import hd_article_category
from helpdesk.helpdesk.doctype.hd_article_category.hd_article_category import (
    SEPARATOR,
    batched_article_index,
    format_category_label,
    get_category_labels,
    get_parent,
    get_stricter_visibility,
    get_subcategories,
    move_category_articles,
    validate_keeps_content,
)
from helpdesk.search import NUM_RESULTS
from helpdesk.utils import is_agent

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
    "parent_article_category",
]
SEARCH_LIMIT = NUM_RESULTS
SEARCH_QUERY_LENGTH = 200
WORDS_PER_MINUTE = 200
LIST_LIMIT = 100
SUBCATEGORY_ARTICLES_LIMIT = 5
# the sidebar reads its titles in one request; newer ones win past this
TITLES_LIMIT = 1000
# within a category, heavier articles list first
WEIGHT_ORDER = "weight desc"

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
def delete_articles(articles: list[str]) -> None:
    """Delete the given HD Articles, clearing them from the tickets that cite them.
    Needs delete permission. Refuses to delete the last article left in a category."""
    # before any raw delete below
    frappe.has_permission("HD Article", "delete", throw=True)
    for name in articles:
        _delete_article(name)


@frappe.whitelist(methods=["POST"])
def archive_articles(articles: list[str]) -> None:
    """Archive the given HD Articles: they leave their category, and tickets keep their
    link. Needs write permission. Refuses to empty a category."""
    frappe.has_permission("HD Article", "write", throw=True)
    for name in articles:
        _archive_article(name)


@frappe.whitelist(methods=["POST"])
def bulk_delete(
    articles: list[str] | None = None,
    categories: list[str] | None = None,
    archive_linked: bool = False,
) -> dict:
    """The KB list's Delete: delete `categories` with their whole branch, and
    `articles`. `archive_linked` archives the ones a ticket cites instead. One request,
    so a failure anywhere leaves everything as it was. Returns {"archived": count}."""
    # before any read or raw delete below
    frappe.has_permission("HD Article", "delete", throw=True)
    archived = sum(
        delete_category(category, with_articles=True, archive_linked=archive_linked)[
            "archived"
        ]
        for category in categories or []
    )
    return {"archived": archived + _delete_or_archive(articles or [], archive_linked)}


@frappe.whitelist()
def get_cited_articles(
    articles: list[str] | None = None, categories: list[str] | None = None
) -> list[str]:
    """Which of `articles`, and of the articles in `categories` and their
    Subcategories, a ticket cites. Needs delete permission on HD Article."""
    frappe.has_permission("HD Article", "delete", throw=True)
    names = set(articles or [])
    if categories:
        branches = [
            name
            for category in categories
            for name in hd_article_category.get_branch(category)
        ]
        names.update(
            frappe.get_all(
                "HD Article", filters={"category": ["in", branches]}, pluck="name"
            )
        )
    return _get_cited_articles(list(names))


def _delete_or_archive(articles: list[str], archive_linked: bool) -> int:
    """Delete `articles`; with `archive_linked`, archive the ones a ticket cites
    instead. Returns how many were archived."""
    archive = _get_archivable(articles) if cint(archive_linked) else set()
    with batched_article_index():
        for name in articles:
            if name in archive:
                _archive_article(name)
            else:
                _delete_article(name)
    return len(archive)


def _get_archivable(articles: list[str]) -> set[str]:
    """Which of `articles` a ticket cites and that aren't archived yet."""
    cited = _get_cited_articles(articles)
    return set(
        frappe.get_all(
            "HD Article",
            filters={"name": ["in", cited], "status": ["!=", "Archived"]},
            pluck="name",
        )
        if cited
        else []
    )


def _get_cited_articles(articles: list[str]) -> list[str]:
    if not articles:
        return []
    return frappe.get_all(
        "HD Ticket",
        filters={"source_article": ["in", articles]},
        pluck="source_article",
        distinct=True,
    )


def _archive_article(name: str) -> None:
    # a save, for version history and the search index
    article = frappe.get_doc("HD Article", name)
    article.status = "Archived"
    article.save()


def _delete_article(name: str) -> None:
    """Delete it, clearing it from the tickets that cite it."""
    if frappe.db.exists("HD Ticket", {"source_article": name}):
        frappe.has_permission("HD Ticket", "write", throw=True)
        # the field is empty once the article no longer exists
        frappe.db.set_value(
            "HD Ticket",
            {"source_article": name},
            "source_article",
            None,
            update_modified=False,
        )
    # feedback would fail the link check
    frappe.db.delete("HD Article Feedback", {"article": name})
    frappe.delete_doc("HD Article", name)


@frappe.whitelist(methods=["POST"])
def create_category(
    title: str,
    icon: str | None = None,
    parent: str | None = None,
    description: str | None = None,
):
    """Create an article category holding one "New Article"; returns both names.
    Under `parent` when given, as a Subcategory. Returns {"article": name,
    "category": name}. "General" is a reserved name."""
    if title.strip().lower() == "general":
        frappe.throw(
            _(
                "General is a reserved category name. Please use a different name to proceed."
            )
        )
    category = frappe.new_doc(
        "HD Article Category",
        category_name=title,
        description=description,
        icon=icon,
        parent_article_category=parent,
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
    """The visibility all of a category's articles share, or None when they differ.
    One of Public, Customers or Private. Needs write access to HD Article."""
    frappe.has_permission("HD Article", "write", throw=True)
    _validate_category(category)
    return hd_article_category.get_category_visibility(category)


@frappe.whitelist()
def get_category_access() -> dict[str, str]:
    """Each top-level category's access across its branch, `Mixed` when its articles differ; empty ones are left out."""
    frappe.has_permission("HD Article", "write", throw=True)
    # one level deep, so a branch is a category and its children
    top = {
        row.name: row.parent_article_category or row.name
        for row in frappe.get_all(
            "HD Article Category", fields=["name", "parent_article_category"]
        )
    }
    branches = {}
    for row in frappe.get_all(
        "HD Article",
        filters={"category": ["is", "set"]},
        fields=["category", "visibility", "status"],
        distinct=True,
    ):
        if name := top.get(row.category):
            branches.setdefault(name, []).append(row)
    access = {}
    for name, rows in branches.items():
        values = hd_article_category.read_visibilities(rows)
        access[name] = values.pop() if len(values) == 1 else "Mixed"
    return access


def category_label_sort_key(label: str) -> tuple:
    """General first, then by label parts so a Subcategory follows its parent."""
    parts = label.split(SEPARATOR)
    return (parts[0] != "General", [part.casefold() for part in parts])


@frappe.whitelist()
def get_category_options() -> list[dict]:
    """Every article category as a picker option, General first, Subcategories after
    their parent. Each has value, label, parent_article_category, icon and
    has_subcategories. Needs write access to HD Article."""
    frappe.has_permission("HD Article", "write", throw=True)
    rows = frappe.get_all(
        "HD Article Category", fields=["name", "parent_article_category", "icon"]
    )
    labels = get_category_labels([row.name for row in rows])
    parents = {row.parent_article_category for row in rows}
    options = [
        {
            "value": row.name,
            "label": labels[row.name],
            "parent_article_category": row.parent_article_category,
            "icon": row.icon,
            "has_subcategories": row.name in parents,
        }
        for row in rows
    ]
    return sorted(options, key=lambda option: category_label_sort_key(option["label"]))


@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def search_categories(
    doctype: str,
    txt: str,
    searchfield: str,
    start: int,
    page_len: int,
    filters: dict | list | None,
) -> list[tuple[str, str]]:
    """Link search for article categories, a Subcategory labelled `Parent › Sub`.
    Matches the label or the name."""
    # ponytail: filters in Python; categories number in the dozens
    names = frappe.get_list("HD Article Category", filters=filters or {}, pluck="name")
    labels = get_category_labels(names)
    txt = (txt or "").casefold()
    rows = sorted(
        (
            (name, label)
            for name, label in labels.items()
            if txt in label.casefold() or txt == name.casefold()
        ),
        key=lambda row: category_label_sort_key(row[1]),
    )
    start, page_len = int(start), int(page_len)
    return rows[start : start + page_len]


@frappe.whitelist(methods=["POST"])
def set_category_visibility(category: str, visibility: str):
    """Set the visibility of every article in a category.
    `visibility` is Public, Customers or Private. Saves each article, so each gets a
    version. Needs write access to HD Article."""
    frappe.has_permission("HD Article", "write", throw=True)
    _validate_category(category)
    options = frappe.get_meta("HD Article").get_options("visibility").split("\n")
    if visibility not in options:
        frappe.throw(_("Invalid access: {0}").format(visibility))
    # saved one by one for version history
    with batched_article_index():
        for name in frappe.get_all(
            "HD Article",
            filters={
                "category": ["in", hd_article_category.get_branch(category)],
                "visibility": ["!=", visibility],
            },
            pluck="name",
        ):
            article = frappe.get_doc("HD Article", name)
            article.visibility = visibility
            article.save()


@frappe.whitelist(methods=["POST"])
def move_to_category(category: str, articles: list[str]):
    """Move the given articles to a category; an archived one comes back as a Draft.
    An article wider than the visibility the category's articles share is narrowed to
    it. Needs write access to HD Article."""
    frappe.has_permission("HD Article", "write", throw=True)
    _validate_category(category)

    # read before the move changes it
    category_visibility = hd_article_category.get_joining_visibility(category)
    for name in articles:
        article = frappe.get_doc("HD Article", name)
        if article.status == "Archived":
            article.status = "Draft"
        article.category = category
        article.visibility = get_stricter_visibility(
            article.visibility, category_visibility
        )
        article.save()


# Guest endpoints: make_article_filters limits guests to Public articles.
@frappe.whitelist(allow_guest=True, methods=["GET"])  # nosemgrep
def get_articles(
    category: str | None = None,
    limit: int | None = None,
    sort: str = "latest",
    include_subcategories: bool = False,
    start: int = 0,
) -> list[dict]:
    """List published articles the caller can read: name, title and excerpt.
    Optionally of one category, and its Subcategories with `include_subcategories`,
    heaviest first, at most 100 from `start`. `sort` "popular" orders by views, else
    newest first. Guests only when the knowledge base is public."""
    validate_public_access()
    filters = make_article_filters()
    order_by = "views desc" if sort == "popular" else "published_on desc"
    if category:
        filters["category"] = (
            ["in", hd_article_category.get_branch(category)]
            if cint(include_subcategories)
            else category
        )
        order_by = f"{WEIGHT_ORDER}, {order_by}"
    return frappe.get_all(
        "HD Article",
        filters=filters,
        fields=["name", "title", "excerpt"],
        # `name` keeps ties in one order, so pages never overlap
        order_by=f"{order_by}, name",
        limit_start=max(cint(start), 0),
        limit_page_length=min(cint(limit) or LIST_LIMIT, LIST_LIMIT),
    )


@frappe.whitelist(allow_guest=True, methods=["GET"])  # nosemgrep
def get_featured_articles(names: str | list | None = None) -> list[dict]:
    """The home page's Featured articles: name, title and excerpt, in pin order.
    `names` reads Settings Preview's unsaved pins instead, in their order. Never
    Private articles, at most MAX_PINNED_ARTICLES. Guests only when the knowledge base
    is public."""
    validate_public_access()
    filters = make_article_filters()
    # Featured is for customers, so agents skip Private too; others keep their narrower filter.
    filters.setdefault("visibility", ["!=", PRIVATE])
    fields = ["name", "title", "excerpt"]
    if names is None:
        filters["pinned"] = 1
        return frappe.get_all(
            "HD Article",
            filters=filters,
            fields=fields,
            order_by="pinned_order asc",
            limit_page_length=MAX_PINNED_ARTICLES,
        )
    names = _parse_guest_names(names, LIST_LIMIT)
    if not names:
        return []
    filters["name"] = ["in", names]
    # the cap cuts after their order
    rows = frappe.get_all("HD Article", filters=filters, fields=fields)
    position = {name: index for index, name in enumerate(names)}
    rows.sort(key=lambda row: position[row.name])
    return rows[:MAX_PINNED_ARTICLES]


@frappe.whitelist(methods=["POST"])
def set_pinned_articles(names: list[str]) -> None:
    """Pin `names` to the home page in that order and unpin every other article.
    At most 5, all Published and not Private. Leaves weights and `modified` alone, and
    doesn't save each article. Needs write access to HD Article."""
    frappe.has_permission("HD Article", "write", throw=True)
    names = list(dict.fromkeys(names))
    if len(names) > MAX_PINNED_ARTICLES:
        throw_pin_limit()
    pinnable = frappe.get_all(
        "HD Article",
        filters={
            "name": ["in", names or [""]],
            "status": "Published",
            "visibility": ["!=", PRIVATE],
        },
        pluck="name",
    )
    if len(pinnable) != len(names):
        frappe.throw(_("Only published articles customers can read can be pinned"))
    article = frappe.qb.DocType("HD Article")
    unpin = (
        frappe.qb.update(article)
        .set(article.pinned, 0)
        .set(article.pinned_order, 0)
        .where(article.pinned == 1)
    )
    if names:
        unpin = unpin.where(article.name.notin(names))
    unpin.run()
    for order, name in enumerate(names, 1):
        frappe.db.set_value(
            "HD Article",
            name,
            {"pinned": 1, "pinned_order": order},
            update_modified=False,
        )


def _parse_guest_names(value, limit: int) -> list[str]:
    """Guest input: a name or a JSON list of names. Bad JSON is a plain name, junk is dropped."""
    if isinstance(value, str) and value.lstrip().startswith("["):
        with suppress(Exception):
            value = frappe.parse_json(value)
    names = [value] if isinstance(value, str) else value
    if not isinstance(names, list):
        return []
    return [name for name in names if isinstance(name, str) and name][:limit]


@frappe.whitelist(allow_guest=True, methods=["GET"])  # nosemgrep
def get_subcategory_articles(category: str) -> dict[str, list[dict]]:
    """The articles of each Subcategory of `category`, heaviest then newest first,
    skipping empty ones."""
    validate_public_access()
    subcategories = get_subcategories(category)
    if not subcategories:
        return {}
    # one query for all; like the sidebar, newer ones win past TITLES_LIMIT
    result = {}
    for row in frappe.get_all(
        "HD Article",
        filters=make_article_filters(category=["in", subcategories]),
        fields=["name", "title", "category"],
        order_by=f"{WEIGHT_ORDER}, published_on desc",
        limit_page_length=TITLES_LIMIT,
    ):
        rows = result.setdefault(row.pop("category"), [])
        if len(rows) < SUBCATEGORY_ARTICLES_LIMIT:
            rows.append(row)
    return result


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
    """Knowledge base sidebar: readable categories, each with its articles' titles.
    get_categories' rows plus `creators` (author name and image) and `articles` (name
    and title, heaviest then newest first). Guests only when the knowledge base is
    public."""
    validate_public_access()
    articles = {}
    for row in frappe.get_all(
        "HD Article",
        filters=make_article_filters(category=["is", "set"]),
        fields=["name", "title", "category"],
        order_by=f"{WEIGHT_ORDER}, published_on desc",
        limit_page_length=TITLES_LIMIT,
    ):
        articles.setdefault(row.pop("category"), []).append(row)
    categories = _get_categories(with_creators=True)
    for category in categories:
        category.articles = articles.get(category.name, [])
    return categories


@frappe.whitelist(allow_guest=True, methods=["GET"])  # nosemgrep
def get_article(name: str) -> dict:
    """Get a readable article: content, author, category, reading time, caller's vote.
    `name` may be the URL path `<name>-<title slug>`. `feedback` is 0 none, 1 helpful,
    2 not helpful. Agents also get `pinned` and `weight`. Doesn't count a view (see
    increment_views). Guests only when the knowledge base is public."""
    name = _get_article_name(name)
    # the desk article page shows the pin and edits the weight
    desk_fields = ["pinned", "weight"] if is_agent() else []
    article = _get_viewable_article(
        name, [*PUBLIC_ARTICLE_FIELDS, "content", *desk_fields]
    )
    article.author = _get_byline(article.author)
    article.title_slug = cleanup_page_name(article.title)
    # archived articles have no category
    category = (
        frappe.db.get_value(
            "HD Article Category",
            article.category,
            [
                "category_name",
                "parent_article_category",
                "parent_article_category.category_name as parent_category_name",
            ],
            as_dict=True,
        )
        if article.category
        else None
    ) or frappe._dict()
    article.category_name = category.category_name
    article.parent_article_category = category.parent_article_category
    article.parent_category_name = category.parent_category_name
    article.category_label = category.category_name and format_category_label(
        category.category_name, category.parent_category_name
    )
    article.feedback = _get_own_feedback(name)
    article.minutes = _get_reading_minutes(
        BeautifulSoup(article.content or "", "html.parser")
    )
    return article


@frappe.whitelist(allow_guest=True, methods=["GET"])  # nosemgrep
def get_article_markdown(name: str) -> None:
    """Download a readable article as a Markdown file, `<name>.md`.
    Served inline, title as the heading. Takes the bare name, not the URL slug. Guests
    only when the knowledge base is public."""
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
    """List categories that have a published article the caller can read, directly or
    in a Subcategory. Each has name, category_name, description, icon, pinned,
    pinned_order, parent_article_category, label, article_count (Subcategories
    included) and last_updated; sorted by category_name. Guests only when the
    knowledge base is public."""
    validate_public_access()
    return _get_categories()


def _get_categories(with_creators: bool = False) -> list[dict]:
    counts, authors, updated = {}, {}, {}
    for category, author, total, modified in frappe.get_all(
        "HD Article",
        filters=make_article_filters(category=["is", "set"]),
        fields=[
            "category",
            "author",
            {"COUNT": "*", "as": "total"},
            {"MAX": "modified", "as": "modified"},
        ],
        group_by="category, author",
        order_by="total desc",
        as_list=True,
    ):
        counts[category] = counts.get(category, 0) + total
        authors.setdefault(category, []).append(author)
        updated[category] = max(updated.get(category, modified), modified)
    if not counts:
        return []
    parents = dict(
        frappe.get_all(
            "HD Article Category",
            filters={
                "name": ["in", list(counts)],
                "parent_article_category": ["is", "set"],
            },
            fields=["name", "parent_article_category"],
            as_list=True,
        )
    )
    # a parent counts its Subcategories' readable Articles too
    for sub, parent in parents.items():
        counts[parent] = counts.get(parent, 0) + counts[sub]
        authors.setdefault(parent, []).extend(authors[sub])
        updated[parent] = max(updated.get(parent, updated[sub]), updated[sub])
    categories = frappe.get_all(
        "HD Article Category",
        filters={"name": ["in", list(counts)]},
        fields=PUBLIC_CATEGORY_FIELDS,
        order_by="category_name asc",
    )
    labels = get_category_labels([category.name for category in categories])
    for category in categories:
        category.article_count = counts[category.name]
        category.last_updated = updated[category.name]
        category.label = labels[category.name]
        if with_creators:
            category.creators = [
                _get_byline(name) for name in dict.fromkeys(authors[category.name])
            ]
    return categories


@frappe.whitelist(allow_guest=True, methods=["GET"])  # nosemgrep
@rate_limit(limit=120, seconds=60, user_based=True)
def search_articles(query: str, limit: int = SEARCH_LIMIT) -> list[dict]:
    """Search published articles the caller can read; returns at most 5 hits.
    Each hit: name, title and excerpt with matches in <mark> tags, title_slug, first
    image, minutes to read, category_name. Empty without RediSearch. Guests only when
    the knowledge base is public."""
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
            fields=[
                "name",
                "content",
                "category",
                "category.category_name as category_name",
            ],
        )
    }
    labels = get_category_labels(list({a.category for a in articles.values()}))
    return [
        _get_search_hit(row, articles[row["name"]], labels)
        for row in hits
        if row["name"] in articles
    ]


def _get_search_hit(row: dict, article: frappe._dict, labels: dict) -> dict:
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
        "category_label": labels.get(article.category),
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
    """Merge one article category into another, deleting the source category.
    Moves every article of `source` to `target`, narrowed to the visibility the
    target's articles share. General can't be the source. Needs delete permission on
    HD Article Category."""
    frappe.has_permission("HD Article Category", "delete", throw=True)

    if source == target:
        frappe.throw(_("Source and target category cannot be same"))
    _validate_category(source)
    _validate_category(target)
    if source == get_general_category():
        frappe.throw(_("Cannot merge General category"))
    if (parent := get_parent(source)) != target:
        validate_keeps_content(parent, leaving_subcategory=source)

    # `source` may lose its last subcategory on the way out
    frappe.flags.deleting_category = [source]
    try:
        with batched_article_index():
            _merge_category(source, target)
    finally:
        frappe.flags.deleting_category = None


def _merge_category(source: str, target: str) -> None:
    if subcategories := get_subcategories(source):
        if target in subcategories:
            _set_parent(target, None)
            subcategories.remove(target)
        elif get_parent(target):
            names = dict(
                frappe.get_all(
                    "HD Article Category",
                    filters={"name": ["in", [source, target]]},
                    fields=["name", "category_name"],
                    as_list=True,
                )
            )
            frappe.throw(
                _(
                    "{0} has subcategories, and {1} is a subcategory. Move its subcategories first, or merge into a top-level category."
                ).format(frappe.bold(names[source]), frappe.bold(names[target]))
            )
        for subcategory in subcategories:
            _set_parent(subcategory, target)
    move_category_articles(source, target)
    frappe.delete_doc("HD Article Category", source)


def _set_parent(category: str, parent: str | None) -> None:
    """Saves, so the parent rules and the article narrowing run."""
    doc = frappe.get_doc("HD Article Category", category)
    doc.parent_article_category = parent
    doc.save()


@frappe.whitelist()
def get_category_delete_summary(category: str) -> dict:
    """What deleting `category` and its Subcategories would touch.
    Returns {"articles": count, "subcategories": count, "cited": count of articles a
    ticket cites}. Needs delete permission on HD Article Category."""
    frappe.has_permission("HD Article Category", "delete", throw=True)
    _validate_category(category)
    branch = hd_article_category.get_branch(category)
    articles = frappe.get_all(
        "HD Article", filters={"category": ["in", branch]}, pluck="name"
    )
    return {
        "articles": len(articles),
        "subcategories": len(branch) - 1,
        "cited": len(_get_cited_articles(articles)),
    }


@frappe.whitelist(methods=["POST"])
def delete_category(
    category: str, with_articles: bool = False, archive_linked: bool = False
) -> dict:
    """Delete an article category. Its articles move to the parent, or General, and
    its Subcategories move up. `with_articles` deletes the whole branch instead;
    `archive_linked` archives the articles a ticket cites. Needs delete permission.
    Returns {"archived": count}."""
    frappe.has_permission("HD Article Category", "delete", throw=True)
    _validate_category(category)
    if category == get_general_category():
        frappe.throw(_("General category can't be deleted"))
    if not with_articles:
        frappe.delete_doc("HD Article Category", category)
        return {"archived": 0}

    # on_trash checks it too, but only after every article is deleted
    validate_keeps_content(
        get_parent(category),
        leaving_subcategory=category,
        message=_("Delete the parent category instead"),
    )
    branch = hd_article_category.get_branch(category)
    frappe.flags.deleting_category = branch
    try:
        articles = frappe.get_all(
            "HD Article", filters={"category": ["in", branch]}, pluck="name"
        )
        archived = _delete_or_archive(articles, archive_linked)
        # subcategories first: the category's on_trash would promote them
        for name in reversed(branch):
            frappe.delete_doc("HD Article Category", name)
    finally:
        frappe.flags.deleting_category = None
    return {"archived": archived}


def get_category_group_options(options: list[dict]) -> list[dict]:
    """Group options of the desk article list: labelled `Parent › Sub`, a Subcategory under its parent."""
    groups = [option for option in options if option["value"]]
    empty = [option for option in options if not option["value"]]
    values = [option["value"] for option in groups]
    # the desk's Edit reads the plain name, description and pin from here
    fields = [
        "name",
        "parent_article_category",
        "category_name",
        "description",
        "pinned",
    ]
    rows = {
        row.name: row
        for row in frappe.get_all(
            "HD Article Category", filters={"name": ["in", values]}, fields=fields
        )
    }
    # a parent's own group is there even when it has no rows
    missing = {row.parent_article_category for row in rows.values()} - set(values)
    missing.discard(None)
    for row in frappe.get_all(
        "HD Article Category",
        filters={"name": ["in", list(missing)]},
        fields=[*fields, "icon"],
    ):
        rows[row.name] = row
        groups.append({"value": row.name, "icon": row.icon})
    names = [group["value"] for group in groups]
    labels = get_category_labels(names)
    # read past permissions: would tell a customer a Private subcategory exists
    with_subcategories = (
        set(
            frappe.get_all(
                "HD Article Category",
                filters={"parent_article_category": ["in", names]},
                pluck="parent_article_category",
            )
        )
        if is_agent()
        else set()
    )
    for group in groups:
        # a dangling link has no category to label it
        group["label"] = labels.get(group["value"], group["value"])
        row = rows.get(group["value"], frappe._dict())
        group["parent_article_category"] = row.parent_article_category
        group["category_name"] = row.category_name
        group["description"] = row.description
        group["pinned"] = row.pinned
        group["has_subcategories"] = group["value"] in with_subcategories
    groups.sort(key=lambda group: category_label_sort_key(group["label"]))
    for group in empty:
        # archiving clears an article's category, so this group holds them
        group.update(label=_("Archived"), icon="lucide-archive")
    return groups + empty


@frappe.whitelist()
def get_general_category():
    """Name of the reserved "General" article category, or None."""
    return frappe.db.get_value(
        "HD Article Category", {"category_name": "General"}, "name"
    )


@frappe.whitelist(allow_guest=True, methods=["POST"])  # nosemgrep
def increment_views(article: str):
    """Count one view of a published article, at most once an hour per reader.
    A reader is a signed-in user or a Guest IP. Drafts aren't counted; an article the
    caller can't read throws."""
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
