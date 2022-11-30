import frappe
from zang import Configuration, ConnectorFactory, HttpMethod, ZangException
from frappe import _


@frappe.whitelist()
def make_call(ticket_id, to):
	"""Make a call to the given number"""

	from_ = "1234"  # this is shown as the caller id
	to = "+917012043162"  # TODO: Remove this line
	# call_to = phone_no
	if not frappe.db.exists("Ticket", ticket_id):
		frappe.throw(_("Ticket does not exist"))
	if not frappe.db.exists("Agent", {"user": frappe.session.user}):
		frappe.throw(_("Calls can only be made by agents"))
	ticket = frappe.get_doc("Ticket", ticket_id)
	if not frappe.db.exists("Contact", ticket.contact):
		frappe.throw(_("Contact does not exist"))

	agent = frappe.get_doc("Agent", {"user": frappe.session.user})
	contact = frappe.get_doc("Contact", ticket.contact)

	# TODO: this block should be removed, once proper avaya api calls can be made -----------
	call_log = frappe.get_doc(
		{
			"doctype": "Avaya Call Log",
			"call_sid": "temp sid",
			"from": from_,
			"to": to,
			"agent_ref": agent.name,
			"contact_ref": contact.name,
			"ticket_ref": ticket.name,
			"status": "queued",
		}
	)
	call_log = call_log.insert(ignore_permissions=True)
	print("call_log", call_log.name)

	return call_log.name
	# Till here	-------------------------------------

	avaya_settings = frappe.get_doc("Avaya Settings")
	account_sid = avaya_settings.account_sid
	auth_token = avaya_settings.auth_token

	configuration = Configuration(account_sid, auth_token)
	calls_connector = ConnectorFactory(configuration).callsConnector

	try:
		call = calls_connector.makeCall(
			to=to,
			from_=from_,
			url="TestUrl",  # url to call when the call is connected
			method=HttpMethod.POST,
			fallbackUrl="FallbackUrl",
			fallbackMethod=HttpMethod.POST,
			statusCallback="StatusCallback",  # url to call when the call status changes
			statusCallbackMethod=HttpMethod.POST,
			heartbeatUrl="HeartbeatUrl",  # url to call every 60 seconds
			heartbeatMethod=HttpMethod.POST,
			# forwardedFrom='1234',
			# playDtmf='123#',
			# timeout=122,
			# hideCallerId=True,
			record=True,
			recordCallback="RecordCallback",  # url to call when the recording is complete
			recordCallbackMethod=HttpMethod.POST,
			# transcribe=True,
			# transcribeCallback='TranscribeCallback',
			# straightToVoicemail=True,
			# ifMachine=IfMachine.REDIRECT,
			# ifMachineUrl='IfMachineUrl',
			# ifMachineMethod=HttpMethod.GET,
			# sipAuthUsername='username',
			# sipAuthPassword='password'
		)
		print(call.sid)
		call_log = frappe.get_doc(
			{
				"doctype": "Avaya Call Log",
				"call_sid": call.sid,
				"from": from_,
				"to": to,
				"agent_ref": agent.name,
				"contact_ref": contact.name if contact else None,
				"status": call.status,
			}
		)

		return call_log

	except ZangException as ze:
		frappe.throw(_("Error making call: {0}").format(ze))


@frappe.whitelist()
def end_call(call_log_id):
	"""End the call"""

	avaya_settings = frappe.get_doc("Avaya Settings")
	account_sid = avaya_settings.account_sid
	auth_token = avaya_settings.auth_token

	configuration = Configuration(account_sid, auth_token)
	calls_connector = ConnectorFactory(configuration).callsConnector

	call_log = frappe.get_doc("Avaya Call Log", call_log_id)
	call = calls_connector.endCall(call_log.call_sid)
	call_log.status = call.status
	call_log.save(ignore_permissions=True)

	return call_log
