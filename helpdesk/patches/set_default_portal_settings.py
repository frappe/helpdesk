from helpdesk.setup.install import set_portal_defaults


def execute():
    """Set the portal's default role and home page for helpdesk.

    Safe to re-run: only fills values that are still empty.
    """
    set_portal_defaults()
