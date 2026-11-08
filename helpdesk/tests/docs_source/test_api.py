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

    def test_refusals_are_not_enqueued(self):
        frappe.set_user(self.manager)
        result = import_docs("http://docs.example.com", self.category)
        self.assertEqual(result["state"], "error")
        self.assertIn("https://", result["message"])
        with patch(ENQUEUED, return_value=True):
            result = import_docs(URL, self.category)
        self.assertIn("already running", result["message"])
        for category in ("No such category", ["a"], None):
            with self.assertRaises(frappe.DoesNotExistError, msg=category):
                import_docs(URL, category)
        self.enqueue.assert_not_called()

    def test_import_enqueues_one_long_job(self):
        frappe.set_user(self.manager)
        result = import_docs(f"{URL}:8443/docs/?x=1", self.category)

        self.assertEqual((result["state"], result["host"]), ("running", HOST))
        self.enqueue.assert_called_once()
        call = self.enqueue.call_args
        self.assertEqual(call.args[0], run_import)
        self.assertEqual(call.kwargs["queue"], "long")
        self.assertEqual(call.kwargs["job_id"], JOB_ID)
        self.assertTrue(call.kwargs["deduplicate"])
        self.assertTrue(call.kwargs["enqueue_after_commit"])
        self.assertEqual(call.kwargs["url"], f"{URL}:8443/docs")


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

    def test_stores_plain_errors_and_logs_unexpected_ones(self):
        patch_docs_site(self, {})
        run_import(URL, self.category)
        result = frappe.cache.get_value(RESULT_KEY)
        self.assertEqual(result["state"], "error")
        self.assertIn("llms.txt or sitemap.xml", result["message"])

        with (
            patch(
                "helpdesk.docs_source.importer.DocsImport.run",
                side_effect=RuntimeError("secret detail"),
            ),
            patch("helpdesk.docs_source.importer.frappe.log_error") as log,
        ):
            run_import(URL, self.category)
        message = frappe.cache.get_value(RESULT_KEY)["message"]
        self.assertNotIn("secret", message)
        self.assertIn("Error Log", message)
        log.assert_called_once()


class TestImportResult(DocsApiCase):
    def test_result_states(self):
        frappe.set_user(self.manager)
        self.assertIsNone(get_import_result())

        running = {"state": "running", "stage": "reading", "done": 3, "total": 9}
        running["host"] = HOST
        frappe.cache.set_value(RESULT_KEY, running)
        with patch(ENQUEUED, return_value=True):
            self.assertEqual(get_import_result(), running)

        result = get_import_result()  # the job is gone
        self.assertEqual((result["state"], result["host"]), ("error", HOST))
        self.assertIn("stopped before it finished", result["message"])
