from unittest.mock import patch

import frappe
from frappe.flow.knowledge.ingest import ingest_source
from frappe.tests import IntegrationTestCase
from frappe.tests.utils import change_settings

from helpdesk.api.ai_search import (
    add_skill,
    add_source,
    get_skills,
    get_sources,
    remove_skill,
    remove_source,
    resync_source,
    set_source_visibility,
)
from helpdesk.api.knowledge_base import answer_question
from helpdesk.test_utils import (
    clear_ai_sources,
    enable_ai_search,
    fake_flow_knowledge,
    fake_web,
    make_agent,
    make_agent_manager,
    make_contact,
    make_private_file,
    reset_ai_question_counts,
    unique_email,
    unique_name,
)

DOCS = "https://docs.example.com/wifi"
PAGE = "<html><body><p>Restart the wifi router to fix wifi. {fact}</p></body></html>"


class TestKnowledgeSources(IntegrationTestCase):
    """An admin adds web pages and files for the assistant to read, each for one audience."""

    def setUp(self) -> None:
        self.enterContext(change_settings("HD Settings", public_knowledge_base=1))
        self.enterContext(patch("frappe.enqueue"))
        enable_ai_search()
        reset_ai_question_counts()
        self.enterContext(fake_flow_knowledge())
        clear_ai_sources()
        self.web = {DOCS: PAGE.format(fact="DOCS-FACT")}
        self.enterContext(fake_web(self.web))

    def add_and_sync(self, **kwargs) -> dict:
        source = add_source(**kwargs)
        ingest_source(source["name"])
        return source

    def listed(self, name: str) -> dict:
        return next(row for row in get_sources() if row["name"] == name)

    def test_a_new_source_is_public_and_syncing(self) -> None:
        source = add_source(source_type="URL", url=DOCS)

        self.assertEqual(source["visibility"], "Public")
        self.assertEqual(source["status"], "Syncing")
        self.assertEqual(self.listed(source["name"])["url"], DOCS)

    def test_a_synced_source_is_ready(self) -> None:
        source = self.add_and_sync(source_type="URL", url=DOCS)

        self.assertEqual(self.listed(source["name"])["status"], "Ready")

    def test_a_source_that_fails_to_sync_says_why(self) -> None:
        source = add_source(source_type="URL", url=DOCS)
        # as Flow's worker records it; a real failed job rolls back the test's own insert
        frappe.db.set_value(
            "Flow Knowledge Source",
            source["name"],
            {
                "status": "Failed",
                "error_log": "Traceback (most recent call last):\n  ...\n"
                "requests.exceptions.HTTPError: 500 Server Error\n",
            },
        )

        row = self.listed(source["name"])
        self.assertEqual(row["status"], "Failed")
        self.assertEqual(row["error"], "500 Server Error")

    def test_a_link_that_does_not_open_is_refused(self) -> None:
        with self.assertRaisesRegex(frappe.ValidationError, "404"):
            add_source(source_type="URL", url="https://docs.example.com/missing")

    def test_a_link_to_an_internal_address_is_refused(self) -> None:
        with (
            patch("socket.getaddrinfo", return_value=[(2, 1, 6, "", ("10.0.0.5", 0))]),
            self.assertRaises(frappe.ValidationError),
        ):
            add_source(source_type="URL", url=DOCS)

    def test_only_pdf_md_and_txt_files_are_taken(self) -> None:
        for name in ("guide.md", "guide.txt"):
            add_source(source_type="File", file_url=make_private_file(unique_name("g") + name))
        with self.assertRaisesRegex(frappe.ValidationError, "PDF, MD or TXT"):
            add_source(source_type="File", file_url=make_private_file("guide.docx"))

    def test_a_duplicate_is_refused(self) -> None:
        add_source(source_type="URL", url=DOCS)
        with self.assertRaisesRegex(frappe.ValidationError, "already added"):
            add_source(source_type="URL", url=DOCS, visibility="Agents")

        file_name = unique_name("handbook") + ".md"
        add_source(source_type="File", file_url=make_private_file(file_name))
        with self.assertRaisesRegex(frappe.ValidationError, "already added"):
            add_source(source_type="File", file_url=make_private_file(file_name))

    def test_a_guest_gets_links_to_public_sources_only(self) -> None:
        internal = "https://docs.example.com/internal-wifi"
        self.web[internal] = PAGE.format(fact="INTERNAL-FACT")
        self.add_and_sync(source_type="URL", url=DOCS)
        self.add_and_sync(source_type="URL", url=internal, visibility="Agents")

        with self.set_user("Guest"):
            result = answer_question("How do I fix my wifi?")

        self.assertEqual([link["url"] for link in result["links"]], [DOCS])
        self.assertNotIn("internal-wifi", frappe.as_json(result))

    def test_customers_and_agents_get_the_sources_of_their_audience(self) -> None:
        customers = "https://docs.example.com/customers-wifi"
        internal = "https://docs.example.com/internal-wifi"
        self.web[customers] = PAGE.format(fact="CUSTOMERS")
        self.web[internal] = PAGE.format(fact="INTERNAL")
        self.add_and_sync(source_type="URL", url=customers, visibility="Customers")
        self.add_and_sync(source_type="URL", url=internal, visibility="Agents")

        def links(user) -> set[str]:
            with self.set_user(user):
                return {row["url"] for row in answer_question("wifi")["links"]}

        self.assertEqual(links(make_contact("kb-src")["user"]), {customers})
        self.assertEqual(
            links(make_agent(unique_email("kb-src-agent"))), {customers, internal}
        )

    def test_a_file_source_is_never_linked(self) -> None:
        self.add_and_sync(
            source_type="File",
            file_url=make_private_file(unique_name("wifi") + ".txt", "Fix wifi here"),
        )

        with self.set_user("Guest"):
            result = answer_question("How do I fix my wifi?")

        self.assertEqual(result["links"], [])

    def test_narrowing_a_source_hides_it_from_guests(self) -> None:
        source = self.add_and_sync(source_type="URL", url=DOCS)
        moved = set_source_visibility(source["name"], "Customers")
        ingest_source(moved["name"])

        self.assertEqual(self.listed(moved["name"])["visibility"], "Customers")
        self.assertFalse(frappe.db.exists("Flow Knowledge Source", source["name"]))
        with self.set_user("Guest"):
            self.assertEqual(answer_question("wifi")["links"], [])

    def test_a_removed_source_is_gone(self) -> None:
        source = add_source(source_type="URL", url=DOCS)
        remove_source(source["name"])

        self.assertEqual(get_sources(), [])

    def test_sync_again_starts_over(self) -> None:
        source = self.add_and_sync(source_type="URL", url=DOCS)
        resync_source(source["name"])

        self.assertEqual(self.listed(source["name"])["status"], "Syncing")

    def test_article_sources_are_not_listed(self) -> None:
        from helpdesk.test_utils import make_article
        from helpdesk.ai_search import index_article

        index_article(make_article("Wifi article"))

        self.assertEqual(get_sources(), [])

    def test_only_a_system_manager_manages_sources(self) -> None:
        source = add_source(source_type="URL", url=DOCS)
        with self.set_user(make_agent_manager()):
            for call in (
                get_sources,
                lambda: add_source(source_type="URL", url=DOCS + "2"),
                lambda: remove_source(source["name"]),
                lambda: resync_source(source["name"]),
                lambda: set_source_visibility(source["name"], "Agents"),
            ):
                with self.assertRaises(frappe.PermissionError):
                    call()

    def test_only_helpdesk_sources_can_be_changed(self) -> None:
        other = frappe.get_doc(
            {
                "doctype": "Flow Knowledge Source",
                "knowledge_base": frappe.get_doc(
                    {"doctype": "Flow Knowledge Base", "title": unique_name("Other")}
                )
                .insert()
                .name,
                "source_type": "Text",
                "title": "Other",
                "content": "Other",
            }
        ).insert()

        with self.assertRaises(frappe.DoesNotExistError):
            remove_source(other.name)


class TestSkills(IntegrationTestCase):
    """An admin adds skills, instructions the assistant follows on every answer."""

    def setUp(self) -> None:
        self.enterContext(patch("frappe.enqueue"))
        enable_ai_search(ai_skills=[])
        self.title = unique_name("Friendly tone")

    def agent_skills(self) -> list[str]:
        return frappe.get_all(
            "Flow Agent Skill",
            {"parent": "helpdesk/kb-assistant"},
            pluck="skill",
        )

    def test_a_skill_reaches_the_assistant(self) -> None:
        add_skill(self.title, "Answer in short, friendly sentences.")

        self.assertEqual(self.agent_skills(), [self.title])
        self.assertEqual(
            get_skills(),
            [{"name": self.title, "instructions": "Answer in short, friendly sentences."}],
        )

    def test_a_skill_added_while_ai_is_off_waits_for_it(self) -> None:
        enable_ai_search(enable_ai_search=0)
        add_skill(self.title, "Be brief.")
        enable_ai_search()

        self.assertEqual(self.agent_skills(), [self.title])

    def test_a_skill_survives_a_settings_save(self) -> None:
        add_skill(self.title, "Be brief.")
        enable_ai_search(ai_model="gpt-4.1")

        self.assertEqual(self.agent_skills(), [self.title])

    def test_a_skill_named_like_another_is_refused(self) -> None:
        add_skill(self.title, "Be brief.")
        with self.assertRaises(frappe.ValidationError):
            add_skill(self.title, "Be long.")

    def test_a_removed_skill_is_gone(self) -> None:
        add_skill(self.title, "Be brief.")
        remove_skill(self.title)

        self.assertEqual(self.agent_skills(), [])
        self.assertEqual(get_skills(), [])
        self.assertFalse(frappe.db.exists("Flow Skill", self.title))

    def test_only_a_system_manager_manages_skills(self) -> None:
        add_skill(self.title, "Be brief.")
        with self.set_user(make_agent_manager()):
            for call in (
                get_skills,
                lambda: add_skill(unique_name("Other"), "Be brief."),
                lambda: remove_skill(self.title),
            ):
                with self.assertRaises(frappe.PermissionError):
                    call()
