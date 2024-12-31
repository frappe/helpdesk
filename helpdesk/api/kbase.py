import frappe
from frappe.utils import get_user_info_for_avatar

# from frappe.core.utils import html2text


@frappe.whitelist()
def get_sub_categories_and_articles(category):
    category_title = frappe.get_value("HD Article Category", category, "category_name")
    sub_categories = frappe.get_all(
        "HD Article Category",
        filters={"parent_category": category},
        fields=["name", "category_name", "icon", "parent_category"],
        order_by="creation",
    )
    sub_categories_names = [sub_category["name"] for sub_category in sub_categories]

    article_fields = [
        "name",
        "title",
        "category",
        "published_on",
        "author",
        "subtitle",
        "article_image",
        "_user_tags",
    ]

    direct_articles = frappe.get_all(
        "HD Article",
        filters={"category": category, "status": "Published"},
        fields=article_fields,
    )

    nested_articles = frappe.get_all(
        "HD Article",
        filters={"category": ["in", sub_categories_names], "status": "Published"},
        fields=article_fields,
    )

    category_tree = {
        "root_category": {"category_id": category, "category_name": category_title},
        "sub_categories": [],
        "all_articles": direct_articles,
        "authors": {},
        "children": [],
    }
    # Create a dictionary to store sub-categories by their name
    sub_categories_dict = {sub_cat["name"]: sub_cat for sub_cat in sub_categories}

    # Add nested articles to their respective sub-categories
    for article in nested_articles:
        sub_cat = sub_categories_dict[article["category"]]
        if "articles" not in sub_cat:
            sub_cat["articles"] = []
        sub_cat["articles"].append(article)

    # Add sub-categories to the main tree
    for sub_cat in sub_categories:
        sub_cat_tree = {
            "name": sub_cat["name"],
            "category_name": sub_cat["category_name"],
            "icon": sub_cat["icon"],
            "articles": sub_cat.get("articles", []),
        }
        category_tree["sub_categories"].append(sub_cat_tree)

    all_articles = []
    for sub_cat in category_tree["sub_categories"]:
        all_articles.extend(sub_cat["articles"])

    # get author details
    for article in all_articles:
        author = article["author"]
        if author not in category_tree["authors"]:
            category_tree["authors"][author] = get_user_info_for_avatar(author)

    return category_tree
