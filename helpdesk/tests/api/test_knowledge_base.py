from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase
from frappe.tests.utils import change_settings
from redis.exceptions import ResponseError

from helpdesk.api.article import get_related
from helpdesk.api.knowledge_base import (
    PUBLIC_ARTICLE_FIELDS,
    PUBLIC_CATEGORY_FIELDS,
    create_category,
    delete_articles,
    delete_category,
    get_article,
    get_article_markdown,
    get_articles,
    get_categories,
    get_category_delete_summary,
    get_category_options,
    get_category_visibility,
    get_general_category,
    get_kb_sidebar,
    increment_views,
    merge_category,
    move_to_category,
    search_articles,
    set_category_visibility,
    vote_on_article,
)
from helpdesk.helpdesk.doctype.hd_article.hd_article import CUSTOMERS, PRIVATE, PUBLIC
from helpdesk.helpdesk.doctype.hd_article_category import hd_article_category
from helpdesk.helpdesk.doctype.hd_article_category.hd_article_category import (
    get_category_labels,
    get_subcategories,
)
from helpdesk.test_utils import (
    article_index_jobs,
    category_names,
    category_row,
    create_user,
    make_agent,
    make_article,
    make_article_category,
    make_article_feedback,
    make_contact,
    make_search_hit,
    make_search_page,
    make_subcategory,
    make_ticket,
    misplaced_categories,
    unique_email,
    unique_name,
)

LIST_ROW_FIELDS = {"name", "title", "excerpt"}
BASE_VIEWS = 1_000_000
BYLINE_FIELDS = {"name", "image"}


class TestPublicReads(IntegrationTestCase):
    def setUp(self) -> None:
        self.enterContext(change_settings("HD Settings", public_knowledge_base=1))
        self.category = make_article_category(
            "Fixture Public", description="Fixture description"
        )
        self.published = self.make_article("Fixture published")
        self.draft = self.make_article("Fixture draft", "Draft")

    def make_article(self, title, status="Published", **values) -> str:
        return make_article(title, status, category=self.category.name, **values)

    def titles(self, **kwargs) -> list[str]:
        return [
            row["title"] for row in get_articles(category=self.category.name, **kwargs)
        ]

    def test_every_endpoint_is_reachable_without_a_session(self) -> None:
        for endpoint in (
            get_articles,
            get_article,
            get_article_markdown,
            get_categories,
            get_kb_sidebar,
            vote_on_article,
            increment_views,
        ):
            self.assertIn(endpoint, frappe.guest_methods)

    def test_a_private_knowledge_base_refuses_every_anonymous_read(self) -> None:
        self.enterContext(change_settings("HD Settings", public_knowledge_base=0))
        with self.set_user("Guest"):
            for endpoint, args in (
                (get_articles, ()),
                (get_kb_sidebar, ()),
                (get_categories, ()),
                (get_article, (self.published,)),
                (get_article_markdown, (self.published,)),
                (increment_views, (self.published,)),
            ):
                with self.subTest(endpoint=endpoint.__name__):
                    self.assertRaises(frappe.PermissionError, endpoint, *args)

    def test_a_public_knowledge_base_answers_a_guest(self) -> None:
        with self.set_user("Guest"):
            self.assertEqual(get_article(self.published)["name"], self.published)

    def test_a_signed_in_reader_is_unaffected(self) -> None:
        self.enterContext(change_settings("HD Settings", public_knowledge_base=0))

        self.assertEqual(get_article(self.published)["name"], self.published)

    def test_a_private_knowledge_base_refuses_anonymous_votes(self) -> None:
        self.enterContext(change_settings("HD Settings", public_knowledge_base=0))
        # Validation now refuses this pair, but sites from before it can have it.
        voting = frappe.db.get_single_value(
            "HD Settings", "allow_anonymous_article_voting"
        )
        frappe.db.set_single_value("HD Settings", "allow_anonymous_article_voting", 1)
        self.addCleanup(
            frappe.db.set_single_value,
            "HD Settings",
            "allow_anonymous_article_voting",
            voting,
        )
        with self.set_user("Guest"):
            self.assertRaises(
                frappe.PermissionError, vote_on_article, self.published, 1
            )

    def test_an_article_carries_the_reader_s_own_vote(self) -> None:
        self.assertEqual(get_article(self.published)["feedback"], 0)

        frappe.get_doc("HD Article", self.published).set_feedback(1)

        self.assertEqual(get_article(self.published)["feedback"], 1)

    def test_a_cookieless_guest_is_shown_no_vote(self) -> None:
        frappe.get_doc("HD Article", self.published).set_feedback(1)
        with self.set_user("Guest"):
            self.assertEqual(get_article(self.published)["feedback"], 0)

    def test_lists_only_published_articles(self) -> None:
        self.assertEqual(self.titles(), ["Fixture published"])

    def test_a_guest_cannot_widen_past_published(self) -> None:
        with self.set_user("Guest"):
            self.assertNotIn("Fixture draft", self.titles())

    def test_narrows_to_one_category(self) -> None:
        other = make_article_category("Fixture Other")
        make_article("Fixture elsewhere", category=other.name)

        self.assertEqual(self.titles(), ["Fixture published"])

    def test_limit_caps_the_list(self) -> None:
        self.make_article("Fixture second")

        self.assertEqual(len(self.titles(limit=1)), 1)

    def test_a_row_carries_what_the_list_shows(self) -> None:
        [article] = get_articles(category=self.category.name)

        self.assertEqual(set(article), LIST_ROW_FIELDS)
        self.assertEqual(article.excerpt, "Fixture published")

    def test_an_excerpt_is_the_first_paragraph(self) -> None:
        body = "<h2>Setup</h2><p></p><p>Open <b>Settings</b>.</p><table><td>Role</td></table>"
        article = frappe.get_doc("HD Article", self.published)
        article.content = body
        article.save()

        [row] = get_articles(category=self.category.name)

        self.assertEqual(row.excerpt, "Open Settings.")

    def test_popular_sorts_by_views(self) -> None:
        frappe.db.set_value("HD Article", self.published, "views", BASE_VIEWS)
        self.make_article("Fixture popular", views=BASE_VIEWS + 1)

        self.assertEqual(
            self.titles(sort="popular"), ["Fixture popular", "Fixture published"]
        )

    def test_reads_one_published_article(self) -> None:
        article = get_article(self.published)

        self.assertEqual(article.content, "<p>Fixture published</p>")
        self.assertEqual(article.category_name, "Fixture Public")
        self.assertEqual(article.author["name"], "Administrator")
        self.assertEqual(set(article.author), BYLINE_FIELDS)
        self.assertEqual(
            set(article),
            {
                *PUBLIC_ARTICLE_FIELDS,
                "status",
                "visibility",
                "content",
                "category_name",
                "category_label",
                "parent_article_category",
                "parent_category_name",
                "feedback",
                "minutes",
                "title_slug",
            },
        )
        self.assertEqual(article.minutes, 1)

    def test_a_url_with_a_title_slug_reads_the_article(self) -> None:
        for path_name in (
            f"{self.published}-fixture-published",
            f"{self.published}-a-renamed-title",
        ):
            self.assertEqual(get_article(path_name).name, self.published)

    def test_a_guest_cannot_read_a_draft(self) -> None:
        with self.set_user("Guest"):
            self.assertRaises(frappe.DoesNotExistError, get_article, self.draft)

    def test_an_agent_can_preview_a_draft(self) -> None:
        self.assertEqual(get_article(self.draft).title, "Fixture draft")

    def test_an_unknown_article_is_not_found(self) -> None:
        self.assertRaises(frappe.DoesNotExistError, get_article, "no-such-article")

    def test_an_article_reads_as_markdown(self) -> None:
        name = self.make_article(
            "Fixture markdown",
            content='<h2>Setup</h2><p>Open <b>Settings</b></p><img src="/files/a.png">',
        )
        get_article_markdown(name)

        self.assertEqual(frappe.response.content_type, "text/markdown")
        self.assertEqual(frappe.response.display_content_as, "inline")
        markdown = frappe.response.filecontent
        self.assertTrue(markdown.startswith("# Fixture markdown\n\n## Setup\n"))
        self.assertIn("Open **Settings**", markdown)
        self.assertIn(f"]({frappe.utils.get_url()}/files/a.png)", markdown)

    def test_a_guest_cannot_read_a_draft_as_markdown(self) -> None:
        with self.set_user("Guest"):
            self.assertRaises(
                frappe.DoesNotExistError, get_article_markdown, self.draft
            )

    def test_categories_carry_a_fixed_shape(self) -> None:
        category = category_row(self.category.name)

        self.assertEqual(
            set(category), {*PUBLIC_CATEGORY_FIELDS, "article_count", "label"}
        )

    def test_a_category_counts_only_its_published_articles(self) -> None:
        category = category_row(self.category.name)

        self.assertEqual(category.article_count, 1)

    def test_creators_come_most_prolific_first_without_emails(self) -> None:
        author = make_agent(unique_email("kb-author"), "Fixture Author")
        with self.set_user(author):
            self.make_article("Fixture by author")
            self.make_article("Fixture by author again")

        category = category_row(self.category.name, with_creators=True)

        self.assertEqual(len(category.creators), 2)
        self.assertEqual(
            category.creators[0]["name"],
            frappe.db.get_value("User", author, "full_name"),
        )
        self.assertEqual(set(category.creators[0]), BYLINE_FIELDS)

    def test_a_byline_drops_a_private_image(self) -> None:
        author = make_agent(unique_email("kb-author"), "Fixture Author")
        with self.set_user(author):
            name = self.make_article("Fixture by author")

        for image, expected in (
            ("/private/files/fixture.png", None),
            ("/files/fixture.png", "/files/fixture.png"),
        ):
            user = frappe.get_doc("User", author)
            user.user_image = image
            user.save(ignore_permissions=True)

            self.assertEqual(get_article(name).author["image"], expected)

    def test_a_category_carries_its_description(self) -> None:
        category = category_row(self.category.name)

        self.assertEqual(category.description, "Fixture description")

    def test_a_reader_is_counted_once_an_hour(self) -> None:
        increment_views(self.published)
        increment_views(self.published)

        self.assertEqual(frappe.db.get_value("HD Article", self.published, "views"), 1)

    def test_a_draft_s_views_are_not_counted_for_a_guest(self) -> None:
        with self.set_user("Guest"):
            self.assertRaises(frappe.DoesNotExistError, increment_views, self.draft)
            self.assertEqual(frappe.db.get_value("HD Article", self.draft, "views"), 0)

    def test_an_agent_previewing_a_draft_adds_no_view(self) -> None:
        increment_views(self.draft)

        self.assertEqual(frappe.db.get_value("HD Article", self.draft, "views"), 0)


class TestCustomersOnlyArticles(IntegrationTestCase):
    def setUp(self) -> None:
        self.enterContext(change_settings("HD Settings", public_knowledge_base=1))
        self.customer = make_contact("kb-customer")["user"]
        self.category = make_article_category("Fixture Visibility")
        self.public = self.make_article("Fixture open", PUBLIC)
        self.members = self.make_article("Fixture members", CUSTOMERS)

    def make_article(self, title, visibility) -> str:
        return make_article(
            title, category=self.category.name, visibility=visibility, views=BASE_VIEWS
        )

    def titles(self) -> list[str]:
        return [row["title"] for row in get_articles(category=self.category.name)]

    def test_defaults_to_customers(self) -> None:
        name = make_article("Fixture default", visibility=None)
        self.assertEqual(
            frappe.db.get_value("HD Article", name, "visibility"), CUSTOMERS
        )

    def test_a_guest_is_shown_only_public_articles(self) -> None:
        with self.set_user("Guest"):
            self.assertEqual(self.titles(), ["Fixture open"])

    def test_a_signed_in_reader_is_shown_both(self) -> None:
        self.assertEqual(sorted(self.titles()), ["Fixture members", "Fixture open"])

    def test_a_customer_is_shown_both(self) -> None:
        with self.set_user(self.customer):
            self.assertEqual(sorted(self.titles()), ["Fixture members", "Fixture open"])

    def test_a_user_without_a_customer_role_is_shown_only_public_articles(self) -> None:
        # signed in for another app: no helpdesk customer role
        user = create_user("kb-other-app@example.com").name
        with self.set_user(user):
            self.assertEqual(self.titles(), ["Fixture open"])

    def test_an_private_article_is_shown_to_neither(self) -> None:
        self.make_article("Fixture internal", PRIVATE)
        self.assertIn("Fixture internal", self.titles())

        with self.set_user(self.customer):
            self.assertNotIn("Fixture internal", self.titles())

        with self.set_user("Guest"):
            self.assertNotIn("Fixture internal", self.titles())

    def test_a_customer_cannot_open_an_private_article(self) -> None:
        internal = self.make_article("Fixture internal link", PRIVATE)
        with self.set_user(self.customer):
            self.assertRaises(frappe.DoesNotExistError, get_article, internal)

    def test_a_guest_cannot_open_one_by_name(self) -> None:
        with self.set_user("Guest"):
            self.assertRaises(frappe.DoesNotExistError, get_article, self.members)

    def test_a_guest_does_not_count_it(self) -> None:
        self.assertEqual(self.count(), 2)

        with self.set_user("Guest"):
            self.assertEqual(self.count(), 1)

    def test_a_guest_does_not_see_its_title(self) -> None:
        with self.set_user("Guest"):
            names = [
                row.name for category in get_kb_sidebar() for row in category.articles
            ]
            self.assertIn(self.public, names)
            self.assertNotIn(self.members, names)

    def test_the_sidebar_nests_each_article_under_its_category(self) -> None:
        category = next(
            row for row in get_kb_sidebar() if row.name == self.category.name
        )
        self.assertEqual(
            {row.name for row in category.articles}, {self.members, self.public}
        )
        self.assertEqual(set(category.articles[0]), {"name", "title"})

    def count(self) -> int:
        return category_row(self.category.name).article_count

    def test_a_guest_is_not_shown_a_category_with_nothing_for_them(self) -> None:
        hidden = make_article_category("Fixture Members Only")
        make_article(
            "Fixture members elsewhere",
            category=hidden.name,
            visibility=CUSTOMERS,
        )
        self.assertIn(hidden.name, category_names())

        with self.set_user("Guest"):
            self.assertNotIn(hidden.name, category_names())

    def test_a_customer_is_not_shown_a_category_with_nothing_for_them(self) -> None:
        internal = make_article_category("Fixture Internal Only")
        make_article(
            "Fixture internal elsewhere",
            category=internal.name,
            visibility=PRIVATE,
        )
        drafts = make_article_category("Fixture Drafts Only")
        make_article("Fixture draft elsewhere", "Draft", category=drafts.name)
        self.assertIn(internal.name, category_names())

        with self.set_user(self.customer):
            names = category_names()
            self.assertNotIn(internal.name, names)
            self.assertNotIn(drafts.name, names)

    def test_a_guest_cannot_vote_on_one(self) -> None:
        with self.set_user("Guest"):
            self.assertRaises(
                frappe.DoesNotExistError, vote_on_article, self.members, 1
            )


class TestArticlePermissions(IntegrationTestCase):
    def setUp(self) -> None:
        self.customer = make_contact("kb-reader")["user"]
        self.agent = make_agent(unique_email("kb-agent"))
        self.members = make_article("Fixture perm members", visibility=CUSTOMERS)
        self.internal = make_article("Fixture perm internal", visibility=PRIVATE)
        self.draft = make_article("Fixture perm draft", status="Draft")

    def listed(self) -> set[str]:
        names = [self.members, self.internal, self.draft]
        return set(
            frappe.get_list("HD Article", filters={"name": ["in", names]}, pluck="name")
        )

    def test_a_customer_lists_only_what_the_portal_shows(self) -> None:
        with self.set_user(self.customer):
            self.assertEqual(self.listed(), {self.members})

    def test_a_customer_cannot_open_a_hidden_article(self) -> None:
        with self.set_user(self.customer):
            frappe.get_doc("HD Article", self.members).check_permission("read")
            for name in (self.internal, self.draft):
                with self.assertRaises(frappe.PermissionError):
                    frappe.get_doc("HD Article", name).check_permission("read")

    def test_an_agent_still_reads_everything(self) -> None:
        with self.set_user(self.agent):
            self.assertEqual(self.listed(), {self.members, self.internal, self.draft})

    def test_a_customer_votes_only_through_vote_on_article(self) -> None:
        # vote_on_article holds the rate limit and the one-vote-per-reader rule
        vote = {
            "doctype": "HD Article Feedback",
            "article": self.members,
            "feedback": 1,
        }
        with self.set_user(self.customer):
            with self.assertRaises(frappe.PermissionError):
                frappe.get_doc({**vote, "visitor_id": "forged"}).insert()

    def test_a_check_for_another_user_uses_their_visibility(self) -> None:
        internal = frappe.get_doc("HD Article", self.internal)

        self.assertTrue(frappe.has_permission("HD Article", "read", internal))
        self.assertFalse(
            frappe.has_permission("HD Article", "read", internal, user=self.customer)
        )


class TestCategoryAccess(IntegrationTestCase):
    def setUp(self) -> None:
        self.enterContext(change_settings("HD Settings", public_knowledge_base=1))
        self.customer = make_contact("kb-reader")["user"]
        self.category = make_article_category("Fixture Access")
        self.articles = [
            make_article("Fixture access one", category=self.category.name),
            make_article("Fixture access two", category=self.category.name),
        ]

    def visibility(self, name) -> str:
        return frappe.db.get_value("HD Article", name, "visibility")

    def listed(self, user) -> bool:
        with self.set_user(user):
            return self.category.name in category_names()

    def test_private_hides_the_category_and_everything_in_it(self) -> None:
        set_category_visibility(self.category.name, PRIVATE)

        self.assertEqual({self.visibility(a) for a in self.articles}, {PRIVATE})
        self.assertFalse(self.listed("Guest"))
        self.assertFalse(self.listed(self.customer))

        set_category_visibility(self.category.name, PUBLIC)

        self.assertTrue(self.listed("Guest"))

    def test_rest_keeps_a_private_category_from_customers(self) -> None:
        set_category_visibility(self.category.name, PRIVATE)
        doc = frappe.get_doc("HD Article Category", self.category.name)

        with self.set_user(self.customer):
            self.assertNotIn(
                self.category.name,
                frappe.get_list("HD Article Category", pluck="name"),
            )
            self.assertFalse(frappe.has_permission(doc=doc, ptype="read"))

        set_category_visibility(self.category.name, CUSTOMERS)

        with self.set_user(self.customer):
            self.assertIn(
                self.category.name,
                frappe.get_list("HD Article Category", pluck="name"),
            )
            self.assertTrue(frappe.has_permission(doc=doc, ptype="read"))

    def test_mixed_access_is_read_from_every_article(self) -> None:
        frappe.db.set_value("HD Article", self.articles[0], "visibility", PUBLIC)
        frappe.db.set_value("HD Article", self.articles[1], "visibility", PRIVATE)

        # a non-agent sees only the public article, yet access is mixed
        with self.set_user(self.customer):
            self.assertIsNone(
                hd_article_category.get_category_visibility(self.category.name)
            )

    def test_a_private_draft_does_not_make_access_mixed(self) -> None:
        frappe.db.set_value("HD Article", self.articles[0], "visibility", CUSTOMERS)
        frappe.db.set_value("HD Article", self.articles[1], "visibility", CUSTOMERS)
        make_article(
            "Fixture access draft",
            status="Draft",
            category=self.category.name,
            visibility=PRIVATE,
        )

        self.assertEqual(
            hd_article_category.get_category_visibility(self.category.name), CUSTOMERS
        )

    def test_a_category_of_drafts_reads_its_drafts(self) -> None:
        category = make_article_category(unique_name("Drafts")).name
        for _ in range(2):
            make_article(status="Draft", category=category, visibility=PRIVATE)

        self.assertEqual(hd_article_category.get_category_visibility(category), PRIVATE)

    def test_merging_reindexes_the_moved_articles(self) -> None:
        other = make_article_category(unique_name("Merged"))
        moved = [make_article(category=other.name) for _ in range(2)]

        with patch("frappe.enqueue") as enqueue:
            merge_category(other.name, self.category.name)

        # one job, and not for the target's own articles
        self.assertEqual(article_index_jobs(enqueue), [set(moved)])

    def test_deleting_a_category_reindexes_only_its_articles(self) -> None:
        make_article(category=get_general_category())
        other = make_article_category(unique_name("Deleted"))
        moved = [make_article(category=other.name) for _ in range(2)]

        with patch("frappe.enqueue") as enqueue:
            delete_category(other.name)

        self.assertEqual(article_index_jobs(enqueue), [set(moved)])

    def test_renaming_a_category_reindexes_its_articles(self) -> None:
        category = frappe.get_doc("HD Article Category", self.category.name)
        category.category_name = unique_name("Renamed")

        with patch("frappe.enqueue") as enqueue:
            category.save()

        self.assertEqual(article_index_jobs(enqueue), [set(self.articles)])

    def test_a_category_access_change_saves_each_article(self) -> None:
        before = {
            a: frappe.db.get_value("HD Article", a, "modified") for a in self.articles
        }

        set_category_visibility(self.category.name, PRIVATE)

        for article in self.articles:
            self.assertGreater(
                frappe.db.get_value("HD Article", article, "modified"), before[article]
            )

    def test_an_unknown_access_is_refused(self) -> None:
        self.assertRaises(
            frappe.ValidationError,
            set_category_visibility,
            self.category.name,
            "Everyone",
        )

    def test_a_customer_can_neither_read_nor_set_it(self) -> None:
        with self.set_user(self.customer):
            self.assertRaises(
                frappe.PermissionError, get_category_visibility, self.category.name
            )
            self.assertRaises(
                frappe.PermissionError,
                set_category_visibility,
                self.category.name,
                PUBLIC,
            )

    def test_a_new_article_in_a_private_category_is_private(self) -> None:
        set_category_visibility(self.category.name, PRIVATE)

        new = make_article(
            "Fixture access new", category=self.category.name, visibility=None
        )

        self.assertEqual(self.visibility(new), PRIVATE)

    def test_a_new_article_in_a_public_category_stays_customers(self) -> None:
        new = make_article(
            "Fixture access public", category=self.category.name, visibility=None
        )

        self.assertEqual(self.visibility(new), CUSTOMERS)

    def test_an_explicit_customers_in_a_public_category_is_kept(self) -> None:
        new = make_article(
            "Fixture access kept",
            category=self.category.name,
            visibility=CUSTOMERS,
        )

        self.assertEqual(self.visibility(new), CUSTOMERS)

    def test_a_new_article_in_a_mixed_category_starts_customers(self) -> None:
        frappe.db.set_value("HD Article", self.articles[0], "visibility", PRIVATE)

        new = make_article(
            "Fixture access mixed", category=self.category.name, visibility=None
        )

        self.assertEqual(self.visibility(new), CUSTOMERS)

    def test_an_explicit_access_is_kept(self) -> None:
        new = make_article(
            "Fixture access explicit",
            category=self.category.name,
            visibility=PRIVATE,
        )

        self.assertEqual(self.visibility(new), PRIVATE)

    def test_an_explicit_customers_in_a_private_category_is_private(
        self,
    ) -> None:
        """Customers is also the default, so insert can't tell it from unset."""
        set_category_visibility(self.category.name, PRIVATE)

        new = make_article(
            "Fixture access customers",
            category=self.category.name,
            visibility=CUSTOMERS,
        )

        self.assertEqual(self.visibility(new), PRIVATE)

    def test_a_filter_in_place_of_a_category_is_refused(self) -> None:
        self.assertRaises(
            (frappe.FrappeTypeError, frappe.DoesNotExistError),
            set_category_visibility,
            ["like", "%"],
            PRIVATE,
        )
        self.assertRaises(
            frappe.DoesNotExistError, set_category_visibility, "no-such-one", PUBLIC
        )
        self.assertEqual({self.visibility(a) for a in self.articles}, {PUBLIC})

    def test_moving_in_takes_the_access_the_category_shares(self) -> None:
        set_category_visibility(self.category.name, PRIVATE)
        other = make_article_category("Fixture Access Other")
        moved = make_article("Fixture access moved", category=other.name)
        make_article("Fixture access stays", category=other.name)

        move_to_category(self.category.name, [moved])

        self.assertEqual(self.visibility(moved), PRIVATE)

    def test_moving_into_a_mixed_category_keeps_the_article_s_access(self) -> None:
        frappe.db.set_value("HD Article", self.articles[0], "visibility", PRIVATE)
        other = make_article_category("Fixture Access Other")
        moved = make_article("Fixture access moved", category=other.name)
        make_article("Fixture access stays", category=other.name)

        move_to_category(self.category.name, [moved])

        self.assertEqual(self.visibility(moved), PUBLIC)

    def test_moving_a_category_s_last_article_says_why_it_cannot(self) -> None:
        other = make_article_category("Fixture Access Other")
        last = make_article("Fixture access last", category=other.name)

        with self.assertRaisesRegex(frappe.ValidationError, "at least one article"):
            move_to_category(self.category.name, [last])

    def test_merging_in_takes_the_access_the_category_shares(self) -> None:
        set_category_visibility(self.category.name, PRIVATE)
        other = make_article_category("Fixture Access Merged")
        merged = make_article("Fixture access merged", category=other.name)

        merge_category(other.name, self.category.name)

        self.assertEqual(self.visibility(merged), PRIVATE)

    def test_deleting_a_category_moves_its_articles_into_general_s_access(self) -> None:
        general = get_general_category()
        make_article("Fixture access general", category=general)
        set_category_visibility(general, PRIVATE)
        other = make_article_category("Fixture Access Deleted")
        moved = make_article("Fixture access deleted", category=other.name)

        frappe.delete_doc("HD Article Category", other.name)

        self.assertEqual(
            frappe.db.get_value("HD Article", moved, ["category", "visibility"]),
            (general, PRIVATE),
        )

    def test_moving_into_a_public_category_keeps_a_private_article_private(
        self,
    ) -> None:
        other = make_article_category("Fixture Access Other")
        moved = make_article(
            "Fixture access private", category=other.name, visibility=PRIVATE
        )
        make_article("Fixture access stays", category=other.name)

        move_to_category(self.category.name, [moved])

        self.assertEqual(self.visibility(moved), PRIVATE)

    def test_merging_into_a_public_category_keeps_a_private_article_private(
        self,
    ) -> None:
        other = make_article_category("Fixture Access Merged")
        merged = make_article(
            "Fixture access merged", category=other.name, visibility=PRIVATE
        )

        merge_category(other.name, self.category.name)

        self.assertEqual(self.visibility(merged), PRIVATE)

    def test_deleting_a_category_never_widens_its_articles_access(self) -> None:
        general = get_general_category()
        make_article("Fixture access general", category=general)
        set_category_visibility(general, PUBLIC)
        other = make_article_category("Fixture Access Deleted")
        moved = make_article(
            "Fixture access deleted", category=other.name, visibility=PRIVATE
        )

        frappe.delete_doc("HD Article Category", other.name)

        self.assertEqual(
            frappe.db.get_value("HD Article", moved, ["category", "visibility"]),
            (general, PRIVATE),
        )


class TestSubcategoryAccess(IntegrationTestCase):
    def setUp(self) -> None:
        self.enterContext(change_settings("HD Settings", public_knowledge_base=1))
        self.customer = make_contact("kb-branch-reader")["user"]
        self.parent = make_article_category(unique_name("Fixture Parent")).name
        self.sub = make_subcategory(self.parent).name

    def visibility(self, name) -> str:
        return frappe.db.get_value("HD Article", name, "visibility")

    def readable(self, category) -> bool:
        return category in frappe.get_list(
            "HD Article Category", pluck="name"
        ) and frappe.has_permission("HD Article Category", "read", category)

    def test_a_parent_with_only_a_readable_subcategory_is_shown(self) -> None:
        make_article(category=self.sub)

        # a customer, not Guest: Guest has no role permission on categories
        with self.set_user(self.customer):
            self.assertTrue(self.readable(self.parent))

    def test_a_private_subcategory_keeps_its_parent_hidden(self) -> None:
        make_article(category=self.parent, visibility=PRIVATE)
        make_article(category=self.sub, visibility=PRIVATE)

        with self.set_user(self.customer):
            self.assertFalse(self.readable(self.parent))
            self.assertFalse(self.readable(self.sub))

    def test_access_reads_the_whole_branch(self) -> None:
        make_article(category=self.parent, visibility=CUSTOMERS)
        make_article(category=self.sub, visibility=PUBLIC)

        self.assertIsNone(hd_article_category.get_category_visibility(self.parent))
        self.assertEqual(hd_article_category.get_category_visibility(self.sub), PUBLIC)

    def test_setting_access_rewrites_subcategory_articles(self) -> None:
        make_article(category=self.parent, visibility=PUBLIC)
        make_article(category=self.sub, visibility=CUSTOMERS)

        set_category_visibility(self.parent, PRIVATE)

        self.assertEqual(
            set(
                frappe.get_all(
                    "HD Article",
                    {"category": ["in", [self.parent, self.sub]]},
                    pluck="visibility",
                    distinct=True,
                )
            ),
            {PRIVATE},
        )

    def test_setting_access_queues_one_index_job_for_the_branch(self) -> None:
        articles = [
            make_article(category=self.parent),
            make_article(category=self.sub),
            make_article(category=self.sub),
        ]

        with patch("frappe.enqueue") as enqueue:
            set_category_visibility(self.parent, PRIVATE)

        self.assertEqual(article_index_jobs(enqueue), [set(articles)])

    def test_getting_a_parent_queues_one_index_job(self) -> None:
        make_article(category=self.parent, visibility=PRIVATE)
        category = make_article_category(unique_name("Fixture Joining"))
        articles = [make_article(category=category.name) for _ in range(2)]

        with patch("frappe.enqueue") as enqueue:
            category.update({"parent_article_category": self.parent}).save()

        self.assertEqual(article_index_jobs(enqueue), [set(articles)])

    def give_parent(self, visibility) -> str:
        """A category with one `visibility` article, moved under the parent."""
        category = make_article_category(unique_name("Fixture Joining"))
        article = make_article(category=category.name, visibility=visibility)
        category.update({"parent_article_category": self.parent}).save()
        return article

    def test_getting_a_parent_narrows_its_articles(self) -> None:
        make_article(category=self.parent, visibility=CUSTOMERS)

        self.assertEqual(self.visibility(self.give_parent(PUBLIC)), CUSTOMERS)

    def test_getting_a_parent_never_widens(self) -> None:
        make_article(category=self.parent, visibility=PUBLIC)

        self.assertEqual(self.visibility(self.give_parent(PRIVATE)), PRIVATE)

    def test_a_parent_may_lose_its_last_own_article(self) -> None:
        make_article(category=self.sub)
        article = frappe.get_doc("HD Article", make_article(category=self.parent))
        other = make_article_category(unique_name("Fixture Elsewhere")).name

        article.update({"category": other}).save()

        self.assertEqual(frappe.db.count("HD Article", {"category": self.parent}), 0)

    def test_a_first_article_in_a_new_subcategory_inherits_the_parent(self) -> None:
        make_article(category=self.parent, visibility=PRIVATE)

        article = make_article(category=self.sub, visibility=CUSTOMERS)

        self.assertEqual(self.visibility(article), PRIVATE)

    def test_moving_into_an_empty_subcategory_narrows_to_its_parent(self) -> None:
        make_article(category=self.parent, visibility=PRIVATE)
        other = make_article_category(unique_name("Fixture Source")).name
        make_article(category=other)
        article = make_article(category=other, visibility=CUSTOMERS)

        move_to_category(self.sub, [article])

        self.assertEqual(self.visibility(article), PRIVATE)

    def test_a_new_subcategory_starts_with_an_article_under_its_parent(self) -> None:
        created = create_category(unique_name("Fixture New Sub"), parent=self.parent)

        self.assertEqual(
            frappe.db.get_value(
                "HD Article Category", created["category"], "parent_article_category"
            ),
            self.parent,
        )
        self.assertEqual(
            frappe.db.get_value("HD Article", created["article"], "category"),
            created["category"],
        )

    def private_general_with_a_customers_subcategory(self) -> tuple[str, str]:
        """A sub of an all-Private General, holding one Customers article."""
        general = get_general_category()
        make_article(category=general)
        set_category_visibility(general, PRIVATE)
        sub = make_subcategory(general).name
        article = make_article(category=sub)
        frappe.db.set_value("HD Article", article, "visibility", CUSTOMERS)
        return sub, article

    def test_deleting_a_subcategory_of_general_never_widens(self) -> None:
        sub, article = self.private_general_with_a_customers_subcategory()

        frappe.delete_doc("HD Article Category", sub)

        self.assertEqual(self.visibility(article), PRIVATE)

    def test_merging_a_subcategory_into_its_parent_never_widens(self) -> None:
        sub, article = self.private_general_with_a_customers_subcategory()

        merge_category(sub, get_general_category())

        self.assertEqual(self.visibility(article), PRIVATE)


class TestParentKeepsContent(IntegrationTestCase):
    """A parent keeps an article of its own or a Subcategory."""

    def setUp(self) -> None:
        self.parent = make_article_category(unique_name("Fixture Lone Parent")).name
        self.sub = frappe.get_doc(
            "HD Article Category", make_subcategory(self.parent).name
        )
        make_article(category=self.sub.name)

    def assert_move_refused(self, parent) -> None:
        self.sub.parent_article_category = parent

        with self.assertRaisesRegex(frappe.ValidationError, "would be left empty"):
            self.sub.save()

        self.assertEqual(
            frappe.db.get_value(
                "HD Article Category", self.sub.name, "parent_article_category"
            ),
            self.parent,
        )

    def test_moving_the_only_subcategory_to_the_top_level_is_refused(self) -> None:
        self.assert_move_refused(None)

    def test_moving_the_only_subcategory_to_another_parent_is_refused(self) -> None:
        self.assert_move_refused(
            make_article_category(unique_name("Fixture Other Parent")).name
        )

    def test_a_parent_with_its_own_article_lets_it_go(self) -> None:
        make_article(category=self.parent)
        self.sub.parent_article_category = None

        self.sub.save()

        self.assertIsNone(
            frappe.db.get_value(
                "HD Article Category", self.sub.name, "parent_article_category"
            )
        )


class TestSubcategoryReads(IntegrationTestCase):
    def setUp(self) -> None:
        self.enterContext(change_settings("HD Settings", public_knowledge_base=1))
        self.enterContext(patch("helpdesk.api.article.get_nouns", return_value=[]))
        self.enterContext(
            patch("helpdesk.api.article.get_noun_phrases", return_value=[])
        )
        self.hd_search = self.enterContext(patch("helpdesk.api.article.hd_search"))
        self.parent_name = unique_name("Fixture Billing")
        self.parent = make_article_category(self.parent_name).name
        self.sub_name = unique_name("FAQ")
        self.sub = make_article_category(
            self.sub_name, parent_article_category=self.parent
        ).name
        self.sub_label = f"{self.parent_name} \u203a {self.sub_name}"

    def test_labels_name_the_parent(self) -> None:
        self.assertEqual(
            get_category_labels([self.parent, self.sub]),
            {self.parent: self.parent_name, self.sub: self.sub_label},
        )

    def test_a_parent_counts_its_subcategories(self) -> None:
        make_article(category=self.parent)
        make_article(category=self.sub)
        make_article(category=self.sub)

        self.assertEqual(category_row(self.parent).article_count, 3)
        self.assertEqual(category_row(self.sub).article_count, 2)

    def test_a_parent_counts_only_what_the_reader_reads(self) -> None:
        make_article(category=self.parent)
        make_article(category=self.sub)
        make_article(category=self.sub, visibility=PRIVATE)
        make_article(category=self.sub, visibility=CUSTOMERS)

        with self.set_user("Guest"):
            self.assertEqual(category_row(self.parent).article_count, 2)
        self.assertEqual(category_row(self.parent).article_count, 4)

    def test_a_guest_sees_a_parent_with_only_a_public_subcategory_article(
        self,
    ) -> None:
        make_article(category=self.sub)

        with self.set_user("Guest"):
            self.assertIn(self.parent, category_names())
            self.assertEqual(category_row(self.parent).article_count, 1)

    def test_a_guest_sees_neither_when_the_subcategory_holds_no_public_article(
        self,
    ) -> None:
        make_article(category=self.sub, visibility=PRIVATE)
        make_article(category=self.sub, visibility=CUSTOMERS)

        with self.set_user("Guest"):
            self.assertNotIn(self.parent, category_names())
            self.assertNotIn(self.sub, category_names())

    def test_rows_carry_their_parent(self) -> None:
        make_article(category=self.parent)
        make_article(category=self.sub)

        self.assertEqual(category_row(self.sub).parent_article_category, self.parent)
        self.assertEqual(category_row(self.sub).label, self.sub_label)
        self.assertFalse(category_row(self.parent).parent_article_category)
        self.assertEqual(category_row(self.parent).label, self.parent_name)

    def test_the_sidebar_lists_a_parent_with_only_a_subcategory_article(self) -> None:
        article = make_article(category=self.sub)

        rows = {row.name: row for row in get_kb_sidebar()}

        self.assertEqual(rows[self.parent].article_count, 1)
        self.assertEqual(rows[self.parent].articles, [])
        self.assertEqual(rows[self.parent].creators, rows[self.sub].creators)
        self.assertEqual([a.name for a in rows[self.sub].articles], [article])

    def test_an_article_carries_its_category_label(self) -> None:
        article = get_article(make_article(category=self.sub))

        self.assertEqual(article.category_label, self.sub_label)
        self.assertEqual(article.parent_article_category, self.parent)
        self.assertEqual(article.parent_category_name, self.parent_name)
        self.assertEqual(article.category_name, self.sub_name)

    def test_an_article_without_a_category_has_no_category_fields(self) -> None:
        article = make_article(status="Archived", category=None)

        with self.set_user(make_agent(unique_email("kb-preview"))):
            row = get_article(article)

        for field in (
            "category_name",
            "category_label",
            "parent_article_category",
            "parent_category_name",
        ):
            self.assertIsNone(row[field])

    def test_a_search_hit_carries_its_category_label(self) -> None:
        article = make_article(category=self.sub)
        self.hd_search.return_value = make_search_page(make_search_hit(article))

        [row] = search_articles("anything")

        self.assertEqual(row["category_label"], self.sub_label)
        self.assertEqual(row["category_name"], self.sub_name)

    def test_category_options_put_subcategories_after_their_parent(self) -> None:
        extra = make_article_category(f"{self.parent_name} Extra").name
        rows = {row["value"]: row for row in get_category_options()}
        labels = [row["label"] for row in get_category_options()]

        self.assertLess(labels.index(self.parent_name), labels.index(self.sub_label))
        self.assertLess(
            labels.index(self.sub_label), labels.index(f"{self.parent_name} Extra")
        )
        self.assertEqual(labels[0], "General")
        make_subcategory(get_general_category())
        labels = [row["label"] for row in get_category_options()]
        general_subs = [
            label for label in labels if label.startswith("General \u203a ")
        ]
        self.assertEqual(labels[1 : 1 + len(general_subs)], general_subs)
        self.assertTrue(rows[self.parent]["has_subcategories"])
        self.assertFalse(rows[extra]["has_subcategories"])
        self.assertEqual(rows[self.sub]["parent_article_category"], self.parent)

    def test_category_options_leave_out_the_excluded(self) -> None:
        values = [row["value"] for row in get_category_options(exclude=self.sub)]

        self.assertNotIn(self.sub, values)
        self.assertIn(self.parent, values)

    def test_a_customer_cannot_list_category_options(self) -> None:
        with self.set_user(make_contact("kb-options")["user"]):
            with self.assertRaises(frappe.PermissionError):
                get_category_options()


class TestSearch(IntegrationTestCase):
    def setUp(self) -> None:
        self.enterContext(change_settings("HD Settings", public_knowledge_base=1))
        self.enterContext(patch("helpdesk.api.article.get_nouns", return_value=[]))
        self.enterContext(
            patch("helpdesk.api.article.get_noun_phrases", return_value=[])
        )
        self.hd_search = self.enterContext(patch("helpdesk.api.article.hd_search"))
        category = make_article_category("Fixture Search").name
        self.public = make_article("Fixture zebra crossing", category=category)
        self.members = make_article(
            "Fixture zebra members", category=category, visibility=CUSTOMERS
        )
        self.internal = make_article(
            "Fixture zebra internal", category=category, visibility=PRIVATE
        )
        self.draft = make_article("Fixture zebra draft", "Draft", category=category)
        self.found(self.public, self.members, self.internal, self.draft)

    def found(self, *articles: str) -> None:
        self.hd_search.return_value = make_search_page(
            *[make_search_hit(article) for article in articles]
        )

    def names(self) -> list[str]:
        return [row["name"] for row in search_articles("zebra")]

    def related(self) -> list[str]:
        return [row["name"] for row in get_related("zebra")]

    def test_is_reachable_without_a_session(self) -> None:
        self.assertIn(search_articles, frappe.guest_methods)

    def test_finds_published_articles_only(self) -> None:
        self.assertIn(self.public, self.names())
        self.assertNotIn(self.draft, self.names())

    def test_marks_the_hit_in_escaped_text(self) -> None:
        hit = make_search_hit(self.public)
        hit.update(
            subject="Fixture <b>zebra</b> crossing",
            description="Where the <b>zebra</b> crosses & how",
        )
        self.hd_search.return_value = make_search_page(hit)

        [row] = search_articles("zebra")

        self.assertIn("<mark>zebra</mark>", row["title"])
        self.assertEqual(row["title_slug"], "fixture-zebra-crossing")
        self.assertIn("&amp;", row["excerpt"])
        self.assertNotIn("<b>", row["excerpt"])
        self.assertEqual(row["category_name"], "Fixture Search")

    def test_an_article_found_in_two_sections_is_listed_once(self) -> None:
        self.hd_search.return_value = make_search_page(
            make_search_hit(self.public, "intro"),
            make_search_hit(self.public, "setup"),
        )

        self.assertEqual(self.names(), [self.public])

    def test_a_guest_is_shown_only_public_articles(self) -> None:
        self.assertIn(self.members, self.names())

        with self.set_user("Guest"):
            self.assertIn(self.public, self.names())
            self.assertNotIn(self.members, self.names())
            self.assertNotIn(self.internal, self.names())

    def test_a_private_knowledge_base_refuses_a_guest(self) -> None:
        self.enterContext(change_settings("HD Settings", public_knowledge_base=0))
        with self.set_user("Guest"):
            self.assertRaises(frappe.PermissionError, search_articles, "zebra")

    def test_a_blank_query_matches_nothing(self) -> None:
        self.assertEqual(search_articles("  "), [])
        self.hd_search.assert_not_called()

    def test_limit_caps_the_list(self) -> None:
        self.assertEqual(len(search_articles("zebra", limit=1)), 1)

    def test_a_query_of_only_stopwords_reads_titles(self) -> None:
        # stopwords never reach the index; a unique one keeps the site's titles out
        self.enterContext(
            patch("helpdesk.api.article.get_stopwords", return_value=["quagga"])
        )
        category = make_article_category("Fixture Stopwords").name
        public = make_article("Quagga facts", category=category)
        internal = make_article("Quagga notes", category=category, visibility=PRIVATE)

        with self.set_user("Guest"):
            self.assertEqual(
                [row["name"] for row in search_articles("Quagga")], [public]
            )
        self.assertIn(internal, [row["name"] for row in search_articles("quagga")])
        self.hd_search.assert_not_called()

    def test_a_site_without_redisearch_finds_nothing(self) -> None:
        self.hd_search.side_effect = ResponseError("unknown command 'FT.SEARCH'")

        self.assertEqual(search_articles("zebra"), [])
        self.assertEqual(get_related("zebra"), [])

    def test_related_help_keeps_to_the_reader_s_visibility(self) -> None:
        self.assertIn(self.internal, self.related())

        with self.set_user(make_contact("kb-searcher")["user"]):
            self.assertNotIn(self.internal, self.related())
            self.assertIn(self.members, self.related())

    def test_related_help_links_carry_a_clean_title_slug(self) -> None:
        hit = make_search_hit(self.public)
        hit.subject = "Fixture <b>zebra</b> crossing"
        self.hd_search.return_value = make_search_page(hit)
        self.assertEqual(
            get_related("zebra")[0]["title_slug"], "fixture-zebra-crossing"
        )


class TestCategoryDelete(IntegrationTestCase):
    def setUp(self) -> None:
        self.parent = make_article_category(unique_name("Fixture Doomed")).name
        self.sub = make_subcategory(self.parent).name

    def category(self, article) -> str | None:
        return frappe.db.get_value("HD Article", article, "category")

    def cite(self, article) -> None:
        make_ticket(source_article=article)

    def test_deleting_a_subcategory_moves_its_articles_to_the_parent(self) -> None:
        article = make_article(category=self.sub)

        delete_category(self.sub)

        self.assertFalse(frappe.db.exists("HD Article Category", self.sub))
        self.assertEqual(self.category(article), self.parent)

    def test_deleting_a_category_promotes_its_subcategories(self) -> None:
        own_article = make_article(category=self.parent)
        sub_article = make_article(category=self.sub)

        delete_category(self.parent)

        self.assertIsNone(
            frappe.db.get_value(
                "HD Article Category", self.sub, "parent_article_category"
            )
        )
        self.assertEqual(self.category(own_article), get_general_category())
        self.assertEqual(self.category(sub_article), self.sub)
        self.assertEqual(
            frappe.db.get_value("HD Article Category", self.sub, "is_group"), 1
        )
        self.assertEqual(misplaced_categories(), [])

    def test_deleting_a_subcategory_of_general_keeps_articles_in_general(self) -> None:
        sub = make_subcategory(get_general_category()).name
        article = make_article(category=sub)

        delete_category(sub)

        self.assertEqual(self.category(article), get_general_category())

    def test_branch_delete_removes_subcategories_and_articles(self) -> None:
        branch_articles = [
            make_article(category=self.parent),
            make_article(category=self.sub),
            make_article(category=self.sub, status="Draft"),
        ]

        self.assertEqual(
            delete_category(self.parent, with_articles=True), {"archived": 0}
        )

        self.assertFalse(frappe.db.exists("HD Article Category", self.parent))
        self.assertFalse(frappe.db.exists("HD Article Category", self.sub))
        self.assertFalse(
            frappe.db.exists("HD Article", {"name": ["in", branch_articles]})
        )
        self.assertFalse(frappe.flags.deleting_category)

    def test_branch_delete_archives_cited_articles(self) -> None:
        make_article(category=self.parent)
        # the only article of its subcategory: the length guard must not fire
        cited = make_article(category=self.sub)
        self.cite(cited)

        self.assertEqual(
            delete_category(self.parent, with_articles=True), {"archived": 1}
        )

        self.assertEqual(
            frappe.db.get_value("HD Article", cited, ["status", "category"]),
            ("Archived", None),
        )
        self.assertFalse(frappe.db.exists("HD Article Category", self.sub))

    def test_deleting_an_article_with_feedback_removes_the_feedback(self) -> None:
        make_article(category=self.parent)
        article = make_article(category=self.parent)
        make_article_feedback(article, 1)

        delete_articles([article])

        self.assertFalse(frappe.db.exists("HD Article", article))
        self.assertFalse(frappe.db.exists("HD Article Feedback", {"article": article}))

    def test_deleting_a_cited_article_archives_it(self) -> None:
        make_article(category=self.parent)
        cited = make_article(category=self.parent)
        self.cite(cited)

        self.assertEqual(delete_articles([cited]), {"archived": 1})

        self.assertEqual(frappe.db.get_value("HD Article", cited, "status"), "Archived")

    def test_archiving_the_last_article_outside_a_branch_delete_is_refused(
        self,
    ) -> None:
        cited = make_article(category=self.sub)
        self.cite(cited)

        with self.assertRaisesRegex(frappe.ValidationError, "at least one article"):
            delete_articles([cited])

        self.assertEqual(self.category(cited), self.sub)

    def test_the_summary_counts_the_branch(self) -> None:
        cited = make_article(category=self.parent)
        make_article(category=self.sub)
        make_article(category=self.sub, status="Draft")
        # two tickets, one cited article
        self.cite(cited)
        self.cite(cited)

        self.assertEqual(
            get_category_delete_summary(self.parent),
            {"articles": 3, "subcategories": 1, "cited": 1},
        )

    def test_a_last_subcategory_branch_delete_is_refused(self) -> None:
        article = make_article(category=self.sub)

        with self.assertRaisesRegex(frappe.ValidationError, "Delete the parent"):
            delete_category(self.sub, with_articles=True)

        self.assertTrue(frappe.db.exists("HD Article Category", self.sub))
        self.assertEqual(self.category(article), self.sub)

    def test_a_subcategory_is_deleted_when_the_parent_has_its_own_article(
        self,
    ) -> None:
        make_article(category=self.parent)
        own = make_article(category=self.sub)

        delete_category(self.sub, with_articles=True)

        self.assertFalse(frappe.db.exists("HD Article", own))
        self.assertFalse(frappe.db.exists("HD Article Category", self.sub))

    def test_a_subcategory_is_deleted_when_a_sibling_keeps_the_parent_filled(
        self,
    ) -> None:
        sibling = make_subcategory(self.parent).name
        make_article(category=sibling)
        own = make_article(category=self.sub)

        delete_category(self.sub, with_articles=True)

        self.assertFalse(frappe.db.exists("HD Article", own))
        self.assertFalse(frappe.db.exists("HD Article Category", self.sub))

    def test_deleting_the_last_empty_subcategory_is_refused(self) -> None:
        with self.assertRaisesRegex(frappe.ValidationError, "Delete the parent"):
            delete_category(self.sub)

        self.assertTrue(frappe.db.exists("HD Article Category", self.sub))

    def test_branch_delete_of_a_parent_with_only_subcategory_articles(self) -> None:
        article = make_article(category=self.sub)

        delete_category(self.parent, with_articles=True)

        self.assertFalse(frappe.db.exists("HD Article Category", self.parent))
        self.assertFalse(frappe.db.exists("HD Article Category", self.sub))
        self.assertFalse(frappe.db.exists("HD Article", article))

    def test_general_cannot_be_deleted(self) -> None:
        general = get_general_category()

        with self.assertRaises(frappe.ValidationError):
            delete_category(general, with_articles=True)

        self.assertTrue(frappe.db.exists("HD Article Category", general))

    def test_a_user_without_delete_permission_is_refused(self) -> None:
        article = make_article(category=self.parent)
        customer = make_contact("kb-deleter")["user"]

        with self.set_user(customer):
            with self.assertRaises(frappe.PermissionError):
                delete_category(self.parent, with_articles=True)
            with self.assertRaises(frappe.PermissionError):
                get_category_delete_summary(self.parent)

        self.assertTrue(frappe.db.exists("HD Article", article))


class TestCategoryMerge(IntegrationTestCase):
    def setUp(self) -> None:
        self.parent = make_article_category(unique_name("Fixture Source")).name
        self.sub = make_subcategory(self.parent).name
        self.other_sub = make_subcategory(self.parent).name

    def parent_of(self, category) -> str | None:
        return frappe.db.get_value(
            "HD Article Category", category, "parent_article_category"
        )

    def test_subcategories_follow_into_a_top_level_target(self) -> None:
        target = make_article_category(unique_name("Fixture Target")).name

        merge_category(self.parent, target)

        self.assertFalse(frappe.db.exists("HD Article Category", self.parent))
        self.assertEqual(self.parent_of(self.sub), target)
        self.assertEqual(self.parent_of(self.other_sub), target)
        self.assertEqual(misplaced_categories(), [])

    def test_merging_a_parent_into_another_subcategory_is_refused(self) -> None:
        other_parent = make_article_category(unique_name("Fixture Other")).name
        target = make_subcategory(other_parent).name

        with self.assertRaisesRegex(frappe.ValidationError, "Move its subcategories"):
            merge_category(self.parent, target)

        self.assertTrue(frappe.db.exists("HD Article Category", self.parent))
        self.assertEqual(self.parent_of(self.sub), self.parent)

    def test_merging_into_its_own_subcategory_promotes_it(self) -> None:
        merge_category(self.parent, self.sub)

        self.assertFalse(frappe.db.exists("HD Article Category", self.parent))
        self.assertIsNone(self.parent_of(self.sub))
        self.assertEqual(set(get_subcategories(self.sub)), {self.other_sub})
        self.assertEqual(
            frappe.db.get_value("HD Article Category", self.sub, "is_group"), 1
        )
        self.assertEqual(misplaced_categories(), [])

    def test_a_subcategory_merges_into_its_parent(self) -> None:
        article = make_article(category=self.sub)

        merge_category(self.sub, self.parent)

        self.assertFalse(frappe.db.exists("HD Article Category", self.sub))
        self.assertEqual(
            frappe.db.get_value("HD Article", article, "category"), self.parent
        )

    def test_merging_the_only_subcategory_elsewhere_is_refused(self) -> None:
        parent = make_article_category(unique_name("Fixture Lone")).name
        sub = make_subcategory(parent).name
        article = make_article(category=sub)
        target = make_article_category(unique_name("Fixture Target")).name

        with self.assertRaisesRegex(frappe.ValidationError, "would be left empty"):
            merge_category(sub, target)

        self.assertTrue(frappe.db.exists("HD Article Category", sub))
        self.assertEqual(frappe.db.get_value("HD Article", article, "category"), sub)

    def test_merged_articles_narrow_to_the_target(self) -> None:
        target = make_article_category(unique_name("Fixture Target")).name
        make_article(category=target, visibility=PRIVATE)
        article = make_article(category=self.parent)

        merge_category(self.parent, target)

        self.assertEqual(
            frappe.db.get_value("HD Article", article, ["category", "visibility"]),
            (target, PRIVATE),
        )
