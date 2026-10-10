from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase

from helpdesk.api import article as article_api
from helpdesk.api import knowledge_base
from helpdesk.api.article import get_related
from helpdesk.api.knowledge_base import (
    PUBLIC_ARTICLE_FIELDS,
    PUBLIC_CATEGORY_FIELDS,
    get_article,
    get_article_markdown,
    get_categories,
    get_category_visibility,
    get_public_article,
    get_public_article_titles,
    get_public_articles,
    increment_views,
    merge_category,
    move_to_category,
    search_articles,
    set_article_feedback,
    set_category_visibility,
)
from helpdesk.helpdesk.doctype.hd_article.hd_article import (
    AGENTS_ONLY,
    CUSTOMERS_ONLY,
    PUBLIC,
)
from helpdesk.search_sqlite import HelpdeskArticleSearch
from helpdesk.test_utils import (
    disable_public_knowledge_base,
    enable_anonymous_article_voting,
    enable_public_knowledge_base,
    make_agent,
    make_article,
    make_article_category,
    make_contact,
    unique_email,
)

LIST_ROW_FIELDS = {"name", "title", "excerpt"}
BASE_VIEWS = 1_000_000
BYLINE_FIELDS = {"name", "image"}
TEST_INDEX = "test_knowledge_base_search.db"


class TestPublicReads(IntegrationTestCase):
    """Open to a guest while the knowledge base is public, never wider than published."""

    def setUp(self) -> None:
        enable_public_knowledge_base()
        self.category = make_article_category(
            "Fixture Public", description="Fixture description"
        )
        self.published = self.make_article("Fixture published")
        self.draft = self.make_article("Fixture draft", "Draft")

    def make_article(self, title, status="Published", **values) -> str:
        return make_article(title, status, category=self.category.name, **values)

    def titles(self, **kwargs) -> list[str]:
        return [
            row["title"]
            for row in get_public_articles(category=self.category.name, **kwargs)
        ]

    def test_every_endpoint_is_reachable_without_a_session(self) -> None:
        for endpoint in (
            get_public_articles,
            get_public_article,
            get_public_article_titles,
            get_article_markdown,
            get_categories,
            set_article_feedback,
            increment_views,
        ):
            self.assertIn(endpoint, frappe.guest_methods)

    def test_the_desk_reader_is_not_open_to_guests(self) -> None:
        self.assertNotIn(get_article, frappe.guest_methods)

    def test_a_private_knowledge_base_refuses_every_anonymous_read(self) -> None:
        disable_public_knowledge_base()
        with self.set_user("Guest"):
            for endpoint, args in (
                (get_public_articles, ()),
                (get_public_article_titles, ()),
                (get_categories, ()),
                (get_public_article, (self.published,)),
                (get_article_markdown, (self.published,)),
                (increment_views, (self.published,)),
            ):
                with self.subTest(endpoint=endpoint.__name__):
                    self.assertRaises(frappe.PermissionError, endpoint, *args)

    def test_a_public_knowledge_base_answers_a_guest(self) -> None:
        with self.set_user("Guest"):
            self.assertEqual(get_public_article(self.published)["name"], self.published)

    def test_a_signed_in_reader_is_unaffected(self) -> None:
        disable_public_knowledge_base()

        self.assertEqual(get_public_article(self.published)["name"], self.published)

    def test_a_private_knowledge_base_refuses_anonymous_votes(self) -> None:
        disable_public_knowledge_base()
        enable_anonymous_article_voting()
        with self.set_user("Guest"):
            self.assertRaises(
                frappe.PermissionError, set_article_feedback, self.published, 1
            )

    def test_an_article_carries_the_reader_s_own_vote(self) -> None:
        self.assertEqual(get_public_article(self.published)["feedback"], 0)

        frappe.get_doc("HD Article", self.published).set_feedback(1)

        self.assertEqual(get_public_article(self.published)["feedback"], 1)

    def test_a_cookieless_guest_is_shown_no_vote(self) -> None:
        frappe.get_doc("HD Article", self.published).set_feedback(1)
        with self.set_user("Guest"):
            self.assertEqual(get_public_article(self.published)["feedback"], 0)

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
        [article] = get_public_articles(category=self.category.name)

        self.assertEqual(set(article), LIST_ROW_FIELDS)
        self.assertEqual(article.excerpt, "Fixture published")

    def test_an_excerpt_is_the_first_paragraph(self) -> None:
        """Kept on the article at save time, so a list page parses no bodies."""
        body = "<h2>Setup</h2><p></p><p>Open <b>Settings</b>.</p><table><td>Role</td></table>"
        article = frappe.get_doc("HD Article", self.published)
        article.content = body
        article.save()

        [row] = get_public_articles(category=self.category.name)

        self.assertEqual(row.excerpt, "Open Settings.")

    def test_popular_sorts_by_views(self) -> None:
        frappe.db.set_value("HD Article", self.published, "views", BASE_VIEWS)
        self.make_article("Fixture popular", views=BASE_VIEWS + 1)

        self.assertEqual(
            self.titles(sort="popular"), ["Fixture popular", "Fixture published"]
        )

    def test_reads_one_published_article(self) -> None:
        article = get_public_article(self.published)

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
                "feedback",
            },
        )

    def test_a_url_with_a_title_slug_reads_the_article(self) -> None:
        for path_name in (
            f"{self.published}-fixture-published",
            f"{self.published}-a-renamed-title",
        ):
            self.assertEqual(get_public_article(path_name).name, self.published)

    def test_a_guest_cannot_read_a_draft(self) -> None:
        with self.set_user("Guest"):
            self.assertRaises(frappe.DoesNotExistError, get_public_article, self.draft)

    def test_an_agent_can_preview_a_draft(self) -> None:
        self.assertEqual(get_public_article(self.draft).title, "Fixture draft")

    def test_an_unknown_article_is_not_found(self) -> None:
        self.assertRaises(
            frappe.DoesNotExistError, get_public_article, "no-such-article"
        )

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
        [category] = [
            row for row in get_categories() if row["name"] == self.category.name
        ]

        self.assertEqual(set(category), {*PUBLIC_CATEGORY_FIELDS, "article_count"})

    def test_a_category_counts_only_its_published_articles(self) -> None:
        [category] = [
            row for row in get_categories() if row["name"] == self.category.name
        ]

        self.assertEqual(category.article_count, 1)

    def test_creators_come_most_prolific_first_without_emails(self) -> None:
        author = make_agent(unique_email("kb-author"), "Fixture Author")
        with self.set_user(author):
            self.make_article("Fixture by author")
            self.make_article("Fixture by author again")

        [category] = [
            row
            for row in get_categories(with_creators=True)
            if row["name"] == self.category.name
        ]

        self.assertEqual(category.creator_count, 2)
        self.assertEqual(
            category.creators[0]["name"],
            frappe.db.get_value("User", author, "full_name"),
        )
        self.assertEqual(set(category.creators[0]), BYLINE_FIELDS)

    def test_a_category_carries_its_description(self) -> None:
        [category] = [
            row for row in get_categories() if row["name"] == self.category.name
        ]

        self.assertEqual(category.description, "Fixture description")

    def test_a_reader_is_counted_once_an_hour(self) -> None:
        increment_views(self.published)
        increment_views(self.published)

        self.assertEqual(frappe.db.get_value("HD Article", self.published, "views"), 1)

    def test_a_draft_s_views_are_not_counted_for_a_guest(self) -> None:
        with self.set_user("Guest"):
            self.assertRaises(frappe.DoesNotExistError, increment_views, self.draft)
            self.assertEqual(frappe.db.get_value("HD Article", self.draft, "views"), 0)


class TestCustomersOnlyArticles(IntegrationTestCase):
    """Live, but every anonymous read misses it: lists, tallies, links and votes."""

    def setUp(self) -> None:
        enable_public_knowledge_base()
        self.customer = make_contact("kb-customer")["user"]
        self.category = make_article_category("Fixture Visibility")
        self.public = self.make_article("Fixture open", PUBLIC)
        self.members = self.make_article("Fixture members", CUSTOMERS_ONLY)

    def make_article(self, title, visibility) -> str:
        return make_article(
            title, category=self.category.name, visibility=visibility, views=BASE_VIEWS
        )

    def titles(self) -> list[str]:
        return [
            row["title"] for row in get_public_articles(category=self.category.name)
        ]

    def test_defaults_to_public(self) -> None:
        name = make_article("Fixture default")
        self.assertEqual(frappe.db.get_value("HD Article", name, "visibility"), PUBLIC)

    def test_a_guest_is_shown_only_public_articles(self) -> None:
        with self.set_user("Guest"):
            self.assertEqual(self.titles(), ["Fixture open"])

    def test_a_signed_in_reader_is_shown_both(self) -> None:
        self.assertEqual(sorted(self.titles()), ["Fixture members", "Fixture open"])

    def test_an_agents_only_article_is_shown_to_neither(self) -> None:
        self.make_article("Fixture internal", AGENTS_ONLY)
        self.assertIn("Fixture internal", self.titles())

        with self.set_user(self.customer):
            self.assertNotIn("Fixture internal", self.titles())

        with self.set_user("Guest"):
            self.assertNotIn("Fixture internal", self.titles())

    def test_a_customer_cannot_open_an_agents_only_article(self) -> None:
        internal = self.make_article("Fixture internal link", AGENTS_ONLY)
        with self.set_user(self.customer):
            self.assertRaises(frappe.DoesNotExistError, get_public_article, internal)
            self.assertRaises(frappe.PermissionError, get_article, internal)

    def test_a_guest_cannot_open_one_by_name(self) -> None:
        with self.set_user("Guest"):
            self.assertRaises(
                frappe.DoesNotExistError, get_public_article, self.members
            )
            self.assertRaises(frappe.PermissionError, get_article, self.members)

    def test_a_guest_does_not_count_it(self) -> None:
        self.assertEqual(self.count(), 2)

        with self.set_user("Guest"):
            self.assertEqual(self.count(), 1)

    def test_a_guest_does_not_see_its_title(self) -> None:
        with self.set_user("Guest"):
            names = [row["name"] for row in get_public_article_titles()]
            self.assertIn(self.public, names)
            self.assertNotIn(self.members, names)

    def count(self) -> int:
        [row] = [row for row in get_categories() if row["name"] == self.category.name]
        return row["article_count"]

    def test_a_guest_is_not_shown_a_category_with_nothing_for_them(self) -> None:
        hidden = make_article_category("Fixture Members Only")
        make_article(
            "Fixture members elsewhere",
            category=hidden.name,
            visibility=CUSTOMERS_ONLY,
        )
        self.assertIn(hidden.name, [row["name"] for row in get_categories()])

        with self.set_user("Guest"):
            self.assertNotIn(hidden.name, [row["name"] for row in get_categories()])

    def test_a_customer_is_not_shown_a_category_with_nothing_for_them(self) -> None:
        internal = make_article_category("Fixture Internal Only")
        make_article(
            "Fixture internal elsewhere",
            category=internal.name,
            visibility=AGENTS_ONLY,
        )
        drafts = make_article_category("Fixture Drafts Only")
        make_article("Fixture draft elsewhere", "Draft", category=drafts.name)
        self.assertIn(internal.name, [row["name"] for row in get_categories()])

        with self.set_user(self.customer):
            names = [row["name"] for row in get_categories()]
            self.assertNotIn(internal.name, names)
            self.assertNotIn(drafts.name, names)

    def test_a_guest_cannot_vote_on_one(self) -> None:
        with self.set_user("Guest"):
            self.assertRaises(
                frappe.DoesNotExistError, set_article_feedback, self.members, 1
            )


class TestArticlePermissions(IntegrationTestCase):
    """The framework applies the portal's audience rule, so `/api/resource` does too."""

    def setUp(self) -> None:
        self.customer = make_contact("kb-reader")["user"]
        self.agent = make_agent(unique_email("kb-agent"))
        self.members = make_article("Fixture perm members", visibility=CUSTOMERS_ONLY)
        self.internal = make_article("Fixture perm internal", visibility=AGENTS_ONLY)
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

    def test_a_check_for_another_user_uses_their_audience(self) -> None:
        internal = frappe.get_doc("HD Article", self.internal)

        self.assertTrue(frappe.has_permission("HD Article", "read", internal))
        self.assertFalse(
            frappe.has_permission("HD Article", "read", internal, user=self.customer)
        )


class TestCategoryAccess(IntegrationTestCase):
    """A category's access is the one its articles share; setting it sets them all."""

    def setUp(self) -> None:
        enable_public_knowledge_base()
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
            names = [row["name"] for row in get_categories()]
        return self.category.name in names

    def test_agents_only_hides_the_category_and_everything_in_it(self) -> None:
        set_category_visibility(self.category.name, AGENTS_ONLY)

        self.assertEqual({self.visibility(a) for a in self.articles}, {AGENTS_ONLY})
        self.assertFalse(self.listed("Guest"))
        self.assertFalse(self.listed(self.customer))

        set_category_visibility(self.category.name, PUBLIC)

        self.assertTrue(self.listed("Guest"))

    def test_changing_access_reindexes_every_article(self) -> None:
        """`set_value` skips the hook that reindexes, so search kept the old access."""
        with patch.object(knowledge_base, "reindex_articles") as reindex:
            set_category_visibility(self.category.name, AGENTS_ONLY)

        self.assertCountEqual(reindex.call_args.args[0], self.articles)

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

    def test_a_new_article_takes_the_access_its_category_shares(self) -> None:
        set_category_visibility(self.category.name, CUSTOMERS_ONLY)

        new = make_article("Fixture access new", category=self.category.name)

        self.assertEqual(self.visibility(new), CUSTOMERS_ONLY)

    def test_a_new_article_in_a_mixed_category_starts_public(self) -> None:
        frappe.db.set_value("HD Article", self.articles[0], "visibility", AGENTS_ONLY)

        new = make_article("Fixture access mixed", category=self.category.name)

        self.assertEqual(self.visibility(new), PUBLIC)

    def test_an_explicit_access_is_kept(self) -> None:
        new = make_article(
            "Fixture access explicit",
            category=self.category.name,
            visibility=AGENTS_ONLY,
        )

        self.assertEqual(self.visibility(new), AGENTS_ONLY)

    def test_an_explicit_public_yields_to_the_access_the_category_shares(self) -> None:
        """Public is the field's default too, so an insert cannot tell it from no choice."""
        set_category_visibility(self.category.name, CUSTOMERS_ONLY)

        new = make_article(
            "Fixture access public",
            category=self.category.name,
            visibility=PUBLIC,
        )

        self.assertEqual(self.visibility(new), CUSTOMERS_ONLY)

    def test_a_filter_in_place_of_a_category_is_refused(self) -> None:
        """The framework refuses the type first; the name check stands on its own too."""
        self.assertRaises(
            (frappe.FrappeTypeError, frappe.DoesNotExistError),
            set_category_visibility,
            ["like", "%"],
            AGENTS_ONLY,
        )
        self.assertRaises(
            frappe.DoesNotExistError, set_category_visibility, "no-such-one", PUBLIC
        )
        self.assertEqual({self.visibility(a) for a in self.articles}, {PUBLIC})

    def test_moving_in_takes_the_access_the_category_shares(self) -> None:
        set_category_visibility(self.category.name, AGENTS_ONLY)
        other = make_article_category("Fixture Access Other")
        moved = make_article("Fixture access moved", category=other.name)
        make_article("Fixture access stays", category=other.name)

        move_to_category(self.category.name, [moved])

        self.assertEqual(self.visibility(moved), AGENTS_ONLY)

    def test_moving_into_a_mixed_category_keeps_the_article_s_access(self) -> None:
        frappe.db.set_value("HD Article", self.articles[0], "visibility", AGENTS_ONLY)
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
        set_category_visibility(self.category.name, AGENTS_ONLY)
        other = make_article_category("Fixture Access Merged")
        merged = make_article("Fixture access merged", category=other.name)

        merge_category(other.name, self.category.name)

        self.assertEqual(self.visibility(merged), AGENTS_ONLY)


class TestSearch(IntegrationTestCase):
    """The index answers; the audience gate filters what it found."""

    def setUp(self) -> None:
        enable_public_knowledge_base()
        category = make_article_category("Fixture Search").name
        # A throwaway index holding only the fixtures, so the site's real one is never touched.
        self.search = HelpdeskArticleSearch(db_name=TEST_INDEX)
        self.search.drop_index()
        self.addCleanup(self.search.drop_index)
        self.search._ensure_fts_table()
        for module in (knowledge_base, article_api):
            patcher = patch.object(
                module,
                "HelpdeskArticleSearch",
                lambda: HelpdeskArticleSearch(db_name=TEST_INDEX),
            )
            patcher.start()
            self.addCleanup(patcher.stop)
        body = "<p>Where the <b>zebra</b> crosses & how</p>"
        self.public = make_article(
            "Fixture zebra crossing", category=category, content=body
        )
        self.members = make_article(
            "Fixture zebra members",
            category=category,
            content=body,
            visibility=CUSTOMERS_ONLY,
        )
        self.draft = make_article(
            "Fixture zebra draft", "Draft", category=category, content=body
        )
        self.search.index_documents_by_name(
            "HD Article", [self.public, self.members, self.draft]
        )

    def names(self) -> list[str]:
        return [row["name"] for row in search_articles("zebra")]

    def test_is_reachable_without_a_session(self) -> None:
        self.assertIn(search_articles, frappe.guest_methods)

    def test_finds_published_articles_only(self) -> None:
        self.assertIn(self.public, self.names())
        self.assertNotIn(self.draft, self.names())

    def test_marks_the_hit_in_escaped_text(self) -> None:
        [row] = [row for row in search_articles("zebra") if row["name"] == self.public]

        self.assertIn("<mark>zebra</mark>", row["title"])
        self.assertIn("&amp;", row["excerpt"])
        self.assertNotIn("<b>", row["excerpt"])
        self.assertEqual(row["category_name"], "Fixture Search")
        self.assertIsNone(row["image"])

    def test_a_guest_is_shown_only_public_articles(self) -> None:
        self.assertIn(self.members, self.names())

        with self.set_user("Guest"):
            self.assertIn(self.public, self.names())
            self.assertNotIn(self.members, self.names())

    def test_the_index_itself_keeps_to_the_reader_s_audience(self) -> None:
        """Filtered in the index, so the top hits are readable, not filtered down to nothing."""
        with self.set_user("Guest"):
            names = [row["name"] for row in self.search.search("zebra")["results"]]

            self.assertIn(self.public, names)
            self.assertNotIn(self.members, names)

    def test_a_private_knowledge_base_refuses_a_guest(self) -> None:
        disable_public_knowledge_base()
        with self.set_user("Guest"):
            self.assertRaises(frappe.PermissionError, search_articles, "zebra")

    def test_three_letters_match_the_start_of_a_word(self) -> None:
        self.assertIn(self.public, [row["name"] for row in search_articles("zeb")])

    def test_a_blank_query_matches_nothing(self) -> None:
        self.assertEqual(search_articles("  "), [])

    def test_limit_caps_the_list(self) -> None:
        self.assertEqual(len(search_articles("zebra", limit=1)), 1)

    def test_related_help_keeps_to_the_reader_s_audience(self) -> None:
        internal = make_article(
            "Fixture zebra internal",
            content="<p>zebra</p>",
            visibility=AGENTS_ONLY,
        )
        self.search.index_documents_by_name("HD Article", [internal])
        self.assertIn(internal, self.related())

        with self.set_user(make_contact("kb-searcher")["user"]):
            self.assertNotIn(internal, self.related())

    def related(self) -> list[str]:
        return [row["name"] for row in get_related("zebra")]
