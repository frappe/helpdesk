from helpdesk.search_sqlite import HelpdeskArticleSearch


def execute():
    """The article index gained `visibility`; one built without it has no column to filter on."""
    search = HelpdeskArticleSearch()
    search.drop_index()
    search.build_index()
