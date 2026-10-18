from helpdesk.helpdesk.doctype.hd_settings.helpers import set_customer_home_page

OLD_PORTAL_HOME = "/helpdesk"


def execute():
    set_customer_home_page([OLD_PORTAL_HOME])
