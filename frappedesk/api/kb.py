import frappe


@frappe.whitelist()
def check_if_article_title_exists(title, name=None):
	filters = {"title": ["=", title]}
	if name:
		filters["name"] = ["!=", name]

	return frappe.db.exists("Article", filters)


@frappe.whitelist()
def insert_new_update_existing_categories(new_values, old_values):
	# TODO: optimize this

	# set idx values for all the new_values based on index
	for i in range(len(new_values)):
		new_values[i]["idx"] = i

	to_insert = [
		{key: val for key, val in c.items() if key != "is_new"}
		for c in new_values
		if "is_new" in c
	]
	to_update = [c for c in new_values if "is_new" not in c]

	names_in_old_values = [c["name"] for c in old_values]
	names_in_new_values = [c["name"] if "name" in c else "" for c in new_values]

	to_archive = [c for c in names_in_old_values if c not in names_in_new_values]

	# validate and delete missing categories
	for category in to_archive:
		if frappe.db.exists("Category", {"name": category, "parent_category": category}):
			raise Exception("Cannot archive category with subcategories")
		elif frappe.db.exists("Article", {"category": category}):
			raise Exception("Cannot archive category with articles")
		else:
			frappe.get_doc("Category", category).archive()

	# create new categories if present
	for category in to_insert:
		doc = frappe.new_doc("Category")
		doc.update(category)
		doc.save()

	# update description & category_name
	for category in to_update:
		doc = frappe.get_doc("Category", category["name"])
		doc.update(category)
		doc.save()

	return


@frappe.whitelist()
def update_articles_order_and_status(new_values):
	# set idx values after filtering out articles marked as draft
	to_update = [c for c in new_values if c["status"] == "Published"]
	for i in range(len(to_update)):
		to_update[i]["idx"] = i

	for article in to_update:
		doc = frappe.get_doc("Article", article["name"])
		doc.update(article)
		doc.save()

	to_mark_as_draft = [c["name"] for c in new_values if c["status"] == "Draft"]

	for article in to_mark_as_draft:
		doc = frappe.get_doc("Article", article)
		doc.status = "Draft"
		doc.idx = -1
		doc.save()

	return


@frappe.whitelist(allow_guest=True)
def get_breadcrumbs(docType, docName):
	if docType not in ["Article", "Category"]:
		frappe.throw("Doctype should be either Article or Category")
	return frappe.get_doc(docType, docName).get_breadcrumbs()


@frappe.whitelist(allow_guest=True)
def check_if_article_is_published(article_name):
	return frappe.db.exists("Article", {"name": article_name, "status": "Published"})


@frappe.whitelist()
def move_articles_to_category(articles, category):
	for article in articles:
		doc = frappe.get_doc("Article", article)
		doc.category = category
		doc.save()


@frappe.whitelist()
def set_status_for_articles(articles, status):
	if status not in ["Published", "Draft"]:
		frappe.throw("Invalid status")
	for article in articles:
		doc = frappe.get_doc("Article", article)
		doc.status = status
		doc.save()


@frappe.whitelist()
def delete_articles(articles):
	for article in articles:
		doc = frappe.get_doc("Article", article)
		doc.status = "Archived"
		doc.save()


@frappe.whitelist(allow_guest=True)
def search(text, limit=999):
	# TODO: change limit to 20, once search result page is implemented
	# TODO: filter based on user permissions
	# TODO: optimize search
	# TODO: filter based on user permissions / guest user

	articles = frappe.get_list(
		"Article",
		filters={"status": ["=", "Published"]},
		or_filters={"title": ["like", f"%{text}%"], "content": ["like", f"%{text}%"]},
		fields=["name", "title", "category"],
		order_by="idx",
		limit=limit,
	)

	categories = frappe.get_list(
		"Category",
		filters={"status": ["=", "Published"]},
		or_filters={
			"category_name": ["like", f"%{text}%"],
			"description": ["like", f"%{text}%"],
		},
		fields=["name", "category_name"],
		order_by="idx",
		limit=limit,
	)

	results = []
	for article in articles:
		results.append(
			{
				"doctype": "Article",
				"name": article.name,
				"title": article.title,
				"category": article.category,
			}
		)
	for category in categories:
		results.append(
			{"doctype": "Category", "name": category.name, "title": category.category_name,}
		)

	return results


@frappe.whitelist(allow_guest=True)
def submit_article_feedback(article, score, previous_score=None):
	user = frappe.session.user
	article_doc = frappe.get_doc("Article", article)
	if previous_score is not None:
		if user != "Guest":
			user_article_feedback = frappe.get_value(
				doctype="User Article Feedback",
				filters={"article": article, "user": user,},
				fieldname="name",
			)
			if user_article_feedback:
				user_article_feedback_doc = frappe.get_doc(
					"User Article Feedback", user_article_feedback
				)
				user_article_feedback_doc.feedback = score
				user_article_feedback_doc.save()
			else:
				frappe.throw("User Article Feedback not found")

		if previous_score != score:
			if score == 1:
				article_doc.helpful += 1
				article_doc.not_helpful -= 1
			else:
				article_doc.helpful -= 1
				article_doc.not_helpful += 1
			article_doc.save(ignore_permissions=True)
	else:
		if user != "Guest":
			user_article_feedback_doc = frappe.new_doc("User Article Feedback")
			user_article_feedback_doc.update(
				{"article": article, "user": user, "feedback": score}
			)
			user_article_feedback_doc.save()

		if score == 0:
			article_doc.not_helpful += 1
		elif score == 1:
			article_doc.helpful += 1
		article_doc.save(ignore_permissions=True)


@frappe.whitelist(allow_guest=True)
def increment_article_views(article):
	# TODO: use data to compute related articles, using past viewed articles of the user and giving a rank to each article
	article_doc = frappe.get_doc("Article", article)
	article_doc.views += 1
	article_doc.save(
		ignore_permissions=True
	)  # ignore_permisssion is required to allow guest users to increment views


@frappe.whitelist(allow_guest=True)
def get_article(article):
	# TODO: check if article has gust access enabled
	# TODO: else filter out with required permissions to view the article
	article_doc = frappe.get_doc("Article", article)
	return article_doc


@frappe.whitelist(allow_guest=True)
def get_articles(
	filters, fields, limit=20, order_by="idx",
):
	return frappe.get_list(
		"Article", filters=filters, fields=fields, limit=limit, order_by=order_by,
	)


@frappe.whitelist(allow_guest=True)
def get_categories(
	filters, fields, limit=20, order_by="idx",
):
	return frappe.get_list(
		"Category", filters=filters, fields=fields, limit=limit, order_by=order_by,
	)


@frappe.whitelist(allow_guest=True)
def get_articles_in_ticket(title=None):
	if title == None:
		article_list = frappe.db.get_list("Article", fields=["name", "title", "content"])
	else:
		article_list = frappe.db.get_list(
			"Article",
			fields=["name", "title", "content"],
			filters={"title": ["like", "%{}%".format(title)]},
		)

	return article_list
