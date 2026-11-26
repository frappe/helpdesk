from helpdesk.setup.default_views import add_default_views


def execute():

    # Set standard views as non-public
    add_default_views(for_existing_sites=True)
