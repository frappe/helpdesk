import os
from twilio.rest import Client
import frappe
from twilio.twiml.voice_response import VoiceResponse
from frappedesk.utils import get_public_url
from frappedesk.handler import Twilio


@frappe.whitelist()
def call(contact_id, phone_number, agent_id):
	to = phone_number

	agent = frappe.get_doc("Agent", agent_id)
	if not agent:
		frappe.throw("Agent not found: {0}".format(agent_id))

	twilio_number = frappe.get_value("Agent Call Setting", agent_id, "twilio_number")
	if not twilio_number:
		frappe.throw("Twilio Number not found for agent: {0}".format(agent_id))

	from_ = frappe.get_value("User", agent.user, "phone")
	if not from_:
		frappe.throw("Phone Number not found for agent: {0}".format(agent_id))

	frappe.get_doc(
		{
			"doctype": "FD Twilio Call Log",
			"call_sid": call.sid,
			"twilio_number": twilio_number,
			"to": to,
			"from_": from_,
			"contact": contact_id,
			"agent": agent_id,
			"status": "queued",
		}
	).insert()

	twilio = Twilio.connect()
	if not twilio:
		frappe.throw("Twilio not connected")

	call = twilio.call(
		to=to,
		from_=twilio_number,
		url=get_public_url("/api/method/frappedesk.frappedesk.api.twilio.outbound"),
	)

	# create call log
	# add a hook to update the call log, refer: https://www.twilio.com/docs/voice/tutorials/how-to-retrieve-call-logs/python?code-sample=code-list-all-calls-example&code-language=Python&code-sdk-version=7.x#

	return call.sid


@frappe.whitelist(allow_guest=True)
def outbound(**kwargs):
	args = frappe._dict(kwargs)

	twilio = Twilio.connect()
	if not twilio:
		return

	assert args.AccountSid == twilio.account_sid
	assert args.ApplicationSid == twilio.application_sid

	response = VoiceResponse()

	from_ = frappe.get_value("FD Twilio Call Log", {"call_sid": args.CallSid}, "_from")
	response.number(from_)

	return str(response)
