from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase

from helpdesk.api.docs_source import get_import_result, import_docs
from helpdesk.docs_source.importer import JOB_ID, RESULT_KEY, run_import
from helpdesk.test_utils import (
    create_agent,
    make_agent_manager,
    make_article_category,
    make_docs_site,
    patch_docs_site,
    unique_email,
    unique_name,
)

HOST = "docs.example.com"
URL = f"https://{HOST}"
ENQUEUED = "helpdesk.api.docs_source.is_job_enqueued"


class DocsApiCase(IntegrationTestCase):
    def setUp(self):
        self.enterContext(patch("frappe.db.commit"))
        self.addCleanup(frappe.db.rollback)
        self.addCleanup(frappe.cache.delete_value, RESULT_KEY)
        self.addCleanup(frappe.set_user, "Administrator")
        frappe.cache.delete_value(RESULT_KEY)
        self.category = make_article_category(unique_name("Api")).name
        self.manager = make_agent_manager()
        self.agent = create_agent(unique_email("plain-agent")).name
        self.enqueue = self.enterContext(
            patch("helpdesk.api.docs_source.frappe.enqueue")
        )
        self.enterContext(patch(ENQUEUED, return_value=False))


class TestImportDocs(DocsApiCase):
    def test_non_manager_cannot_import(self):
        for user in (self.agent, "Guest"):
            frappe.set_user(user)
            with self.assertRaises(frappe.PermissionError, msg=user):
                import_docs(URL, self.category)
            with self.assertRaises(frappe.PermissionError, msg=user):
                get_import_result()
        self.enqueue.assert_not_called()

    def test_bad_url_is_answered_with_plain_copy_and_not_enqueued(self):
        frappe.set_user(self.manager)
        result = import_docs("http://docs.example.com", self.category)
        self.assertEqual(result["state"], "error")
        self.assertIn("https://", result["message"])
        self.enqueue.assert_not_called()

    def test_unknown_category_is_refused(self):
        frappe.set_user(self.manager)
        for category in ("No such category", ["a"], None):
            with self.assertRaises(frappe.DoesNotExistError, msg=category):
                import_docs(URL, category)
        self.enqueue.assert_not_called()

    def test_import_enqueues_one_long_job(self):
        frappe.set_user(self.manager)
        result = import_docs(f"{URL}/docs/?x=1", self.category)

        self.assertEqual(result["state"], "running")
        self.enqueue.assert_called_once()
        call = self.enqueue.call_args
        self.assertEqual(call.args[0], run_import)
        self.assertEqual(call.kwargs["queue"], "long")
        self.assertEqual(call.kwargs["job_id"], JOB_ID)
        self.assertTrue(call.kwargs["deduplicate"])
        self.assertTrue(call.kwargs["enqueue_after_commit"])
        self.assertEqual(call.kwargs["url"], f"{URL}/docs")
        self.assertEqual(call.kwargs["category"], self.category)

    def test_second_import_while_running_is_refused(self):
        frappe.set_user(self.manager)
        with patch(ENQUEUED, return_value=True):
            result = import_docs(URL, self.category)
        self.assertEqual(result["state"], "error")
        self.assertIn("already running", result["message"])
        self.enqueue.assert_not_called()

    def test_starting_clears_the_last_result(self):
        frappe.cache.set_value(RESULT_KEY, {"state": "done", "created": 3})
        frappe.set_user(self.manager)
        import_docs(URL, self.category)
        with patch(ENQUEUED, return_value=True):
            self.assertEqual(get_import_result()["state"], "running")


class TestRunImport(DocsApiCase):
    def test_stores_the_counts(self):
        patch_docs_site(self, make_docs_site(HOST, {"a": "Alpha", "b": "Beta"}))
        run_import(URL, self.category)
        self.assertEqual(
            frappe.cache.get_value(RESULT_KEY),
            {
                "state": "done",
                "created": 2,
                "skipped": 0,
                "failed": 0,
                "host": HOST,
                "category": self.category,
            },
        )

    def test_stores_the_plain_error(self):
        patch_docs_site(self, {})
        run_import(URL, self.category)
        result = frappe.cache.get_value(RESULT_KEY)
        self.assertEqual(result["state"], "error")
        self.assertIn("llms.txt or sitemap.xml", result["message"])

    def test_an_unexpected_failure_stores_generic_copy_and_logs(self):
        with (
            patch(
                "helpdesk.docs_source.importer.DocsImport.run",
                side_effect=RuntimeError("secret detail"),
            ),
            patch("helpdesk.docs_source.importer.frappe.log_error") as log,
        ):
            run_import(URL, self.category)
        result = frappe.cache.get_value(RESULT_KEY)
        self.assertEqual(result["state"], "error")
        self.assertNotIn("secret", result["message"])
        self.assertIn("Error Log", result["message"])
        log.assert_called_once()


class TestImportResult(DocsApiCase):
    def test_nothing_before_any_run(self):
        frappe.set_user(self.manager)
        self.assertIsNone(get_import_result())

    def test_reports_running_progress(self):
        running = {
            "state": "running",
            "stage": "reading",
            "done": 3,
            "total": 9,
            "host": HOST,
        }
        frappe.cache.set_value(RESULT_KEY, running)
        frappe.set_user(self.manager)
        with patch(ENQUEUED, return_value=True):
            self.assertEqual(get_import_result(), running)

    def test_running_state_without_job_reports_stopped_error(self):
        frappe.cache.set_value(
            RESULT_KEY,
            {
                "state": "running",
                "stage": "reading",
                "done": 3,
                "total": 9,
                "host": HOST,
            },
        )
        frappe.set_user(self.manager)
        result = get_import_result()
        self.assertEqual(result["state"], "error")
        self.assertEqual(result["host"], HOST)
        self.assertIn("stopped before it finished", result["message"])
        self.assertIn("kept", result["message"])
