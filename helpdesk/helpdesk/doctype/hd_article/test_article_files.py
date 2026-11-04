import os
from unittest.mock import patch

import frappe
from frappe.core.doctype.file.utils import find_file_by_url
from frappe.tests import IntegrationTestCase

from helpdesk.api.knowledge_base import set_category_visibility
from helpdesk.helpdesk.doctype.hd_article.article_files import replace_file_url
from helpdesk.test_utils import create_agent, make_article_category, unique_name

SITE = frappe.utils.get_url


class TestArticleFiles(IntegrationTestCase):
    def setUp(self):
        self.addCleanup(frappe.set_user, "Administrator")

    def make_file(self, article=None, name=None, private=0):
        """A real file on disk, removed when the test ends."""
        file = frappe.get_doc(
            {
                "doctype": "File",
                "file_name": name or f"{frappe.generate_hash(length=10)}.png",
                "content": frappe.generate_hash().encode(),
                "is_private": private,
                "attached_to_doctype": "HD Article" if article else None,
                "attached_to_name": article,
            }
        ).insert(ignore_permissions=True)
        self.addCleanup(self.remove_from_disk, file.name)
        return file

    def remove_from_disk(self, file_name: str):
        if frappe.db.exists("File", file_name):
            frappe.delete_doc("File", file_name, force=True, ignore_permissions=True)

    def make_article(self, visibility="Customers", content="<p>Text</p>", **values):
        return frappe.get_doc(
            {
                "doctype": "HD Article",
                "title": unique_name("Article"),
                "status": "Published",
                "visibility": visibility,
                "content": content,
                "category": make_article_category(unique_name("Files")).name,
                **values,
            }
        ).insert()

    def make_article_with_file(self, visibility="Customers", private=0, **file_values):
        article = self.make_article(visibility)
        file = self.make_file(article.name, private=private, **file_values)
        article.content = f'<p><img src="{file.file_url}"></p>'
        return article, file

    def reload(self, doc):
        return frappe.get_doc(doc.doctype, doc.name)

    def test_narrowing_an_article_makes_its_file_private_and_repoints_the_content(self):
        article, file = self.make_article_with_file("Public")
        article.save()

        article.visibility = "Customers"
        article.save()

        file = self.reload(file)
        self.assertEqual(file.is_private, 1)
        self.assertTrue(file.file_url.startswith("/private/files/"))
        self.assertIn(f'src="{file.file_url}"', self.reload(article).content)
        self.assertTrue(os.path.exists(file.get_full_path()))

    def test_widening_an_article_makes_its_file_public_and_repoints_the_content(self):
        article, file = self.make_article_with_file("Private", private=1)
        article.save()

        article.visibility = "Public"
        article.save()

        file = self.reload(file)
        self.assertEqual(file.is_private, 0)
        self.assertTrue(file.file_url.startswith("/files/"))
        self.assertIn(f'src="{file.file_url}"', self.reload(article).content)

    def test_customers_to_private_keeps_the_url(self):
        article, file = self.make_article_with_file(private=1)
        article.save()
        url = file.file_url

        article.visibility = "Private"
        article.save()

        self.assertEqual(self.reload(file).file_url, url)

    def test_widening_leaves_a_file_the_content_does_not_use_private(self):
        article = self.make_article()
        file = self.make_file(article.name, private=1)

        article.visibility = "Public"
        article.save()

        self.assertEqual(self.reload(file).is_private, 1)

    def test_a_file_uploaded_public_goes_private_on_the_next_save(self):
        article, file = self.make_article_with_file("Customers")

        article.save()

        self.assertEqual(self.reload(file).is_private, 1)

    def test_a_new_article_takes_its_authors_upload(self):
        file = self.make_file()

        article = self.make_article(content=f'<img src="{file.file_url}">')

        file = self.reload(file)
        self.assertEqual(file.attached_to_doctype, "HD Article")
        self.assertEqual(file.attached_to_name, article.name)
        self.assertEqual(file.is_private, 1)
        self.assertIn(file.file_url, self.reload(article).content)

    def test_a_new_article_leaves_another_users_upload(self):
        file = self.make_file()
        frappe.db.set_value("File", file.name, "owner", "Guest")

        self.make_article(content=f'<img src="{file.file_url}">')

        file = self.reload(file)
        self.assertFalse(file.attached_to_name)
        self.assertEqual(file.is_private, 0)

    def test_a_shared_file_keeps_working_for_the_other_article(self):
        article, file = self.make_article_with_file("Public")
        article.save()
        other = self.make_article("Public")
        twin = frappe.copy_doc(file)
        twin.attached_to_name = other.name
        twin.flags.ignore_duplicate_entry_error = True
        twin.insert(ignore_permissions=True)
        self.addCleanup(self.remove_from_disk, twin.name)

        article.visibility = "Customers"
        article.save()

        self.assertEqual(self.reload(twin).is_private, 0)
        self.assertTrue(os.path.exists(self.reload(twin).get_full_path()))
        self.assertTrue(os.path.exists(self.reload(file).get_full_path()))

    def test_the_same_file_attached_twice_ends_private_and_readable(self):
        article, file = self.make_article_with_file("Public")
        article.save()
        twin = frappe.copy_doc(file)
        twin.flags.ignore_duplicate_entry_error = True
        twin.insert(ignore_permissions=True)
        self.addCleanup(self.remove_from_disk, twin.name)

        article.visibility = "Customers"
        article.save()

        self.assertEqual(self.reload(twin).is_private, 1)
        content = self.reload(article).content
        self.assertEqual(content.count("/private/files/"), 1)
        self.assertNotIn('"/files/', content)
        self.assertTrue(os.path.exists(self.reload(twin).get_full_path()))

    def test_a_file_gone_from_disk_does_not_block_the_save(self):
        article, file = self.make_article_with_file("Public")
        article.save()
        os.remove(file.get_full_path())

        article.visibility = "Customers"
        article.save()

        self.assertEqual(self.reload(article).visibility, "Customers")
        self.assertEqual(self.reload(file).is_private, 0)

    def test_a_remote_file_is_left_alone(self):
        article = self.make_article("Public")
        url = "https://example.com/files/photo.png"
        file = frappe.get_doc(
            {
                "doctype": "File",
                "file_name": "photo.png",
                "file_url": url,
                "attached_to_doctype": "HD Article",
                "attached_to_name": article.name,
            }
        ).insert(ignore_permissions=True)
        self.addCleanup(self.remove_from_disk, file.name)

        article.visibility = "Customers"
        article.save()

        self.assertEqual(self.reload(file).file_url, url)
        self.assertEqual(self.reload(file).is_private, 0)

    def test_a_failed_save_puts_the_file_back(self):
        self.addCleanup(frappe.db.commit)
        article, file = self.make_article_with_file("Public")
        article.save()
        frappe.db.commit()
        self.addCleanup(frappe.db.delete, "HD Article Category", article.category)
        self.addCleanup(frappe.db.delete, "HD Article", article.name)
        public_path = file.get_full_path()

        article.visibility = "Customers"
        with patch.object(
            type(article), "on_update", side_effect=frappe.ValidationError
        ):
            with self.assertRaises(frappe.ValidationError):
                article.save()
        frappe.db.rollback()

        self.assertTrue(os.path.exists(public_path))
        self.assertEqual(self.reload(file).is_private, 0)

    def test_stale_content_is_pointed_back_at_the_moved_file(self):
        article, file = self.make_article_with_file("Public")
        article.save()
        stale = self.reload(article).content
        article.visibility = "Customers"
        article.save()

        article = self.reload(article)
        article.content = stale
        article.save()

        self.assertIn(self.reload(file).file_url, self.reload(article).content)

    def test_a_taken_name_renames_the_file_and_repoints_the_content(self):
        name = f"{frappe.generate_hash(length=10)}.png"
        self.make_file(name=name, private=1)
        article, file = self.make_article_with_file("Public", name=name)
        article.save()
        stale = self.reload(article).content

        article.visibility = "Customers"
        article.save()
        file = self.reload(file)
        self.assertNotEqual(file.file_url, f"/private/files/{name}")
        self.assertIn(file.file_url, self.reload(article).content)

        article = self.reload(article)
        article.content = stale
        article.save()
        self.assertIn(file.file_url, self.reload(article).content)

    def test_a_url_another_file_owns_is_not_taken_over(self):
        name = f"{frappe.generate_hash(length=10)}.png"
        other = self.make_file(name=name)
        article = self.make_article()
        file = self.make_file(article.name, name=name, private=1)
        self.assertEqual(file.file_url, "/private" + other.file_url)
        article.content = f'<img src="{other.file_url}">'

        article.save()

        self.assertIn(f'src="{other.file_url}"', self.reload(article).content)

    def test_an_agent_without_file_access_can_change_visibility(self):
        article, file = self.make_article_with_file("Public")
        article.save()
        frappe.db.set_value("File", file.name, "owner", "Administrator")
        create_agent("article-files-agent@example.com")
        frappe.set_user("article-files-agent@example.com")

        article = self.reload(article)
        article.visibility = "Customers"
        article.save()

        frappe.set_user("Administrator")
        self.assertEqual(self.reload(file).is_private, 1)

    def test_changing_a_category_moves_the_files_of_its_articles(self):
        article, file = self.make_article_with_file("Public")
        article.save()

        set_category_visibility(article.category, "Customers")

        self.assertEqual(self.reload(file).is_private, 1)
        self.assertIn(self.reload(file).file_url, self.reload(article).content)

    def test_a_private_file_follows_the_article_for_a_customer(self):
        article, file = self.make_article_with_file()
        article.save()
        file = self.reload(file)
        customer = create_customer_user()

        frappe.set_user(customer)
        self.assertTrue(find_file_by_url(file.file_url))

        frappe.set_user("Administrator")
        article = self.reload(article)
        article.visibility = "Private"
        article.save()
        frappe.set_user(customer)
        self.assertFalse(find_file_by_url(file.file_url))


class TestReplaceFileUrl(IntegrationTestCase):
    def test_a_path_in_an_attribute(self):
        self.assertEqual(
            replace_file_url(
                '<img src="/files/a.png">', "/files/a.png", "/private/files/a.png"
            ),
            '<img src="/private/files/a.png">',
        )

    def test_single_quotes_and_css(self):
        content = (
            "<a href='/files/a.png'></a><p style=\"background: url(/files/a.png)\"></p>"
        )
        self.assertEqual(
            content.replace("/files/", "/private/files/"),
            replace_file_url(content, "/files/a.png", "/private/files/a.png"),
        )

    def test_an_encoded_url(self):
        self.assertEqual(
            replace_file_url(
                '<img src="/files/my%20photo.png">',
                "/files/my photo.png",
                "/private/files/my photo.png",
            ),
            '<img src="/private/files/my%20photo.png">',
        )

    def test_an_escaped_url(self):
        self.assertEqual(
            replace_file_url(
                '<img src="/files/a&amp;b.png">',
                "/files/a&b.png",
                "/private/files/a&b.png",
            ),
            '<img src="/private/files/a%26b.png">',
        )

    def test_an_absolute_url_of_this_site(self):
        self.assertEqual(
            replace_file_url(
                f'<img src="{SITE()}/files/a.png">',
                "/files/a.png",
                "/private/files/a.png",
            ),
            f'<img src="{SITE()}/private/files/a.png">',
        )

    def test_a_url_of_another_site_stays(self):
        content = '<img src="https://docs.frappe.io/files/a.png">'
        self.assertEqual(
            replace_file_url(content, "/files/a.png", "/private/files/a.png"), content
        )

    def test_a_private_url_is_not_prefixed_twice(self):
        content = '<img src="/private/files/a.png">'
        self.assertEqual(
            replace_file_url(content, "/files/a.png", "/private/files/a.png"), content
        )

    def test_a_longer_name_stays(self):
        content = '<a href="/files/a.png.bak"></a>'
        self.assertEqual(
            replace_file_url(content, "/files/a.png", "/private/files/a.png"), content
        )

    def test_a_query_string_is_kept(self):
        self.assertEqual(
            replace_file_url(
                '<img src="/private/files/a.png?fid=x">',
                "/private/files/a.png",
                "/files/a.png",
            ),
            '<img src="/files/a.png?fid=x">',
        )

    def test_text_stays(self):
        content = "<p>Open /files/a.png to see it</p>"
        self.assertEqual(
            replace_file_url(content, "/files/a.png", "/private/files/a.png"), content
        )


def create_customer_user() -> str:
    email = "article-files-customer@example.com"
    if not frappe.db.exists("User", email):
        user = frappe.get_doc(
            {
                "doctype": "User",
                "email": email,
                "first_name": "Customer",
                "send_welcome_email": 0,
                "user_type": "Website User",
            }
        ).insert(ignore_permissions=True)
        user.add_roles("HD Customer")
    return email
