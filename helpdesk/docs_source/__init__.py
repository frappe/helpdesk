import json

import frappe


class DocsSource:
    """What the help center needs from an outside docs site."""

    def search(self, query: str) -> list[dict]:
        raise NotImplementedError

    def get_page(self, route: str) -> dict:
        """Raises frappe.DoesNotExistError for a missing or hidden page."""
        raise NotImplementedError

    def list_pages(self, section: str | None = None) -> list[dict]:
        """Each `{"route", "title", "section"}`."""
        raise NotImplementedError

    def sections(self) -> list[dict]:
        raise NotImplementedError


def get_source() -> DocsSource | None:
    settings = frappe.get_cached_doc("HD Settings")
    if not settings.docs_source_url:
        return None
    # Imported here: source modules import this one.
    from helpdesk.docs_source.llms import LlmsSource
    from helpdesk.docs_source.sitemap import SitemapSource
    from helpdesk.docs_source.wiki import WikiSource

    hidden = json.loads(settings.docs_source_hidden_sections or "[]")
    if settings.docs_source_type == "Frappe Wiki":
        return WikiSource(settings.docs_source_url, hidden)
    if settings.docs_source_type == "llms.txt":
        return LlmsSource(settings.docs_source_url)
    if settings.docs_source_type == "Sitemap":
        return SitemapSource(settings.docs_source_url)
    return None
