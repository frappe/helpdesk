import frappe
from frappedesk.setup.install import (
	enable_track_service_level_agreement_in_support_settings,
)


def execute():
	enable_track_service_level_agreement_in_support_settings()
