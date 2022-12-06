from twilio.rest import Client as TwilioClient

import frappe
from frappe import _
from frappe.utils.password import get_decrypted_password


class Twilio:
	"""Twilio connector over TwilioClient."""

	def __init__(self, settings):
		"""
		:param settings: `Twilio Settings` doctype
		"""
		self.settings = settings
		self.account_sid = settings.account_sid

		self.twilio_client = self.get_twilio_client()

	@classmethod
	def connect(self):
		"""Make a twilio connection."""
		settings = frappe.get_doc("Twilio Settings")
		if not (settings and settings.enabled):
			return
		return Twilio(settings=settings)

	@classmethod
	def get_twilio_client(self):
		twilio_settings = frappe.get_doc("Twilio Settings")
		if not twilio_settings.enabled:
			frappe.throw(_("Please enable twilio settings before sending WhatsApp messages"))

		auth_token = get_decrypted_password(
			"Twilio Settings", "Twilio Settings", "auth_token"
		)
		client = TwilioClient(twilio_settings.account_sid, auth_token)

		return client

	def call(self, to, from_, url):
		"""Make a call."""
		call = self.twilio_client.calls.create(
			twiml=(
				"<Response><Say>This call may be recorded for quality and training"
				" purposes, Please wait your call will be connected with one of our"
				" agents</Say></Response>"
			),
			to=to,
			from_=from_,
			url=url,
		)

		return call
