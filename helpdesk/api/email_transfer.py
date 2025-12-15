import frappe
from frappe import _
from frappe.utils import get_url


INTERNAL_EMAIL_DOMAINS = ["cozycornerpatios.com", "zipcushions.com"]


def extract_customer_email(sender, recipients):
	"""Extract customer email excluding internal domains"""
	all_emails = []
	
	if sender:
		all_emails.append(sender)
	
	if recipients:
		# Recipients can be a string or list
		if isinstance(recipients, str):
			recipient_list = [r.strip() for r in recipients.split(",")]
		else:
			recipient_list = recipients
		all_emails.extend(recipient_list)
	
	# Extract email addresses and filter out internal domains
	customer_emails = []
	for email_str in all_emails:
		# Extract email from format like "Name <email@domain.com>" or just "email@domain.com"
		email = email_str
		if "<" in email_str and ">" in email_str:
			email = email_str.split("<")[1].split(">")[0].strip()
		else:
			email = email_str.strip()
		
		# Check if email domain is internal
		domain = email.split("@")[-1] if "@" in email else ""
		if domain and domain.lower() not in INTERNAL_EMAIL_DOMAINS:
			customer_emails.append(email)
	
	return customer_emails[0] if customer_emails else None


def parse_name_into_first_last(full_name):
	"""Split name into first_name and last_name"""
	if not full_name:
		return "", ""
	
	parts = full_name.strip().split()
	if len(parts) == 0:
		return "", ""
	elif len(parts) == 1:
		return parts[0], ""
	else:
		return parts[0], " ".join(parts[1:])


def create_transfer_notes(source_doc, selected_emails, all_emails):
	"""Generate detailed transfer notes"""
	notes = []
	
	# Source document info
	if source_doc.doctype == "HD Ticket":
		notes.append(f"Transferred from HD Ticket: {source_doc.name}")
		if source_doc.get("subject"):
			notes.append(f"Ticket Subject: {source_doc.subject}")
	else:
		notes.append(f"Transferred from CRM Lead: {source_doc.name}")
		if source_doc.get("first_name") or source_doc.get("last_name"):
			first = source_doc.get('first_name') or ''
			last = source_doc.get('last_name') or ''
			name = f"{first} {last}".strip()
			if name:
				notes.append(f"Lead Name: {name}")
	
	# Email summaries
	if selected_emails:
		notes.append(f"\nTransferred {len(selected_emails)} email(s):")
		for email in selected_emails:
			subject = email.get("subject", "No Subject")
			date = email.get("creation", "")
			notes.append(f"  - {subject} ({date})")
	
	return "\n".join(notes)


def copy_communication(comm_name, target_doctype, target_name):
	"""Duplicate communication with new reference"""
	try:
		original_comm = frappe.get_doc("Communication", comm_name)
		
		# Log original content for debugging
		has_original_content = bool(original_comm.content)
		has_original_text = bool(original_comm.text_content)
		
		# Truncate subject for logging to avoid exceeding 140 char limit
		log_subject = (original_comm.subject or "")[:50]
		
		frappe.log_error(
			f"Original comm {comm_name}: has_content={has_original_content}, has_text_content={has_original_text}, subject={log_subject}",
			"Comm Copy - Original"
		)
		
		# Create new communication and explicitly copy all fields
		# This ensures content and text_content are properly copied
		new_comm = frappe.new_doc("Communication")
		
		# Copy all important fields explicitly
		new_comm.communication_type = original_comm.communication_type or "Communication"
		new_comm.communication_medium = original_comm.communication_medium or "Email"
		new_comm.subject = original_comm.subject
		new_comm.content = original_comm.content  # CRITICAL: Copy content
		new_comm.text_content = original_comm.text_content  # CRITICAL: Copy text_content
		new_comm.sender = original_comm.sender
		new_comm.sender_full_name = original_comm.sender_full_name
		new_comm.recipients = original_comm.recipients
		new_comm.cc = original_comm.cc or ""
		new_comm.bcc = original_comm.bcc or ""
		new_comm.sent_or_received = original_comm.sent_or_received or "Received"
		new_comm.delivery_status = original_comm.delivery_status
		new_comm.email_status = original_comm.email_status
		new_comm.message_id = original_comm.message_id
		new_comm.in_reply_to = original_comm.in_reply_to
		new_comm.email_account = original_comm.email_account
		new_comm.communication_date = original_comm.communication_date or original_comm.creation
		new_comm.uid = original_comm.uid
		new_comm.user = original_comm.user or frappe.session.user
		
		# Set reference to new target
		new_comm.reference_doctype = target_doctype
		new_comm.reference_name = str(target_name)
		new_comm.status = "Linked"
		
		# Clear any timeline_links that might have been set from original
		new_comm.timeline_links = []
		
		# Set flags and insert
		new_comm.flags.ignore_permissions = True
		new_comm.flags.ignore_mandatory = True
		
		try:
			new_comm.insert(ignore_permissions=True)
		except Exception as insert_error:
			# If insert fails, log detailed error
			error_details = f"Failed to insert communication\nOriginal: {comm_name}\nTarget: {target_doctype}/{target_name}\nSender: {original_comm.sender}\nSubject: {original_comm.subject}\nError: {str(insert_error)}\n{frappe.get_traceback()}"
			frappe.log_error(error_details, "Comm Insert Failed")
			raise
		
		# Reload and verify content was saved
		new_comm.reload()
		has_new_content = bool(new_comm.content)
		has_new_text = bool(new_comm.text_content)
		
		frappe.log_error(
			f"New comm {new_comm.name}: has_content={has_new_content}, has_text_content={has_new_text}, target={target_doctype}/{target_name}",
			"Comm Copy - Result"
		)
		
		# If content was lost during insert, try to update it directly
		if has_original_content and not has_new_content:
			frappe.log_error(
				f"Content was lost during insert for {new_comm.name}, attempting to restore",
				"Comm Copy - Content Lost"
			)
			frappe.db.set_value("Communication", new_comm.name, "content", original_comm.content, update_modified=False)
			frappe.db.set_value("Communication", new_comm.name, "text_content", original_comm.text_content, update_modified=False)
			frappe.db.commit()
		
		# Verify the communication exists and has correct reference
		verify_comm = frappe.db.get_value(
			"Communication",
			new_comm.name,
			["reference_doctype", "reference_name", "subject"],
			as_dict=True
		)
		
		if not verify_comm:
			raise Exception(f"Communication {new_comm.name} was not saved to database!")
		
		if verify_comm.reference_doctype != target_doctype or verify_comm.reference_name != target_name:
			frappe.log_error(
				f"WARNING: Communication {new_comm.name} has wrong reference!\nExpected: {target_doctype}/{target_name}\nActual: {verify_comm.reference_doctype}/{verify_comm.reference_name}",
				"Comm Ref Mismatch"
			)
		
		return new_comm.name
	except Exception as e:
		error_msg = f"Error copying communication {comm_name}: {str(e)}\n{frappe.get_traceback()}"
		frappe.log_error(error_msg, "Comm Copy Error")
		raise


@frappe.whitelist()
def get_communications_for_transfer(doctype, name):
	"""Get list of Communication records for transfer"""
	if not frappe.has_permission(doctype, "read", name):
		frappe.throw(_("Not permitted"), frappe.PermissionError)
	
	# Get communication names first
	comm_names = frappe.get_all(
		"Communication",
		filters={
			"reference_doctype": doctype,
			"reference_name": name,
			"communication_medium": "Email",
		},
		fields=["name"],
		order_by="creation asc",
	)
	
	# Load full Communication documents to ensure all fields (especially content) are available
	communications = []
	for comm_name in comm_names:
		try:
			comm = frappe.get_doc("Communication", comm_name.name)
			communications.append({
				"name": comm.name,
				"subject": comm.subject,
				"sender": comm.sender,
				"recipients": comm.recipients,
				"creation": comm.creation,
				"content": comm.content,
				"text_content": comm.text_content,
			})
		except Exception as e:
			frappe.log_error(f"Error loading communication {comm_name.name}: {str(e)}", "Comm Load Error")
			continue
	
	return communications


@frappe.whitelist()
def transfer_to_crm(ticket_name, communication_ids=None, delete_source=True):
	"""Transfer HD Ticket to CRM Lead with selected communications"""
	if not frappe.has_permission("HD Ticket", "read", ticket_name):
		frappe.throw(_("Not permitted"), frappe.PermissionError)
	
	try:
		# Fetch HD Ticket
		ticket = frappe.get_doc("HD Ticket", ticket_name)
		
		# Fetch Contact document to get display name
		customer_name = ""
		if ticket.get("contact"):
			try:
				contact = frappe.get_doc("Contact", ticket.contact)
				if contact.get("first_name") or contact.get("last_name"):
					first = contact.get('first_name') or ''
					last = contact.get('last_name') or ''
					customer_name = f"{first} {last}".strip()
				if not customer_name and contact.get("full_name"):
					customer_name = contact.full_name
			except Exception as e:
				frappe.log_error(f"Error fetching contact {ticket.contact}: {str(e)}")
		
		# If no name from contact, try to get from ticket
		if not customer_name and ticket.get("raised_by"):
			# Extract name from email if possible
			customer_name = ticket.raised_by.split("@")[0] if "@" in ticket.raised_by else ticket.raised_by
		
		# Extract customer information
		customer_email = ticket.get("raised_by")
		customer_phone = ticket.get("contact_number")
		
		# Get all communications to extract email if missing
		all_communications = get_communications_for_transfer("HD Ticket", ticket_name)
		
		frappe.log_error(
			f"Ticket: {ticket_name}\nAll communications found: {len(all_communications)}\nComm IDs: {[c['name'] for c in all_communications]}",
			"Transfer: All Communications"
		)
		
		if not customer_email and all_communications:
			# Try to extract from first communication
			first_comm = all_communications[0]
			customer_email = extract_customer_email(first_comm.get("sender"), first_comm.get("recipients"))
		
		# If still no email, generate a placeholder
		if not customer_email:
			customer_email = f"transferred-{ticket_name}@example.com"
		
		# Parse name into first_name and last_name
		first_name, last_name = parse_name_into_first_last(customer_name)
		
		# Get selected communications
		selected_communications = []
		if communication_ids:
			# Parse communication_ids if it's a string
			if isinstance(communication_ids, str):
				import json
				try:
					communication_ids = json.loads(communication_ids)
				except:
					communication_ids = [communication_ids]
			
			frappe.log_error(
				f"Filtering communications\nRequested IDs: {communication_ids}\nAvailable: {[c['name'] for c in all_communications]}",
				"Transfer: Filter Communications"
			)
			
			selected_communications = [
				comm for comm in all_communications if comm["name"] in communication_ids
			]
			
			frappe.log_error(
				f"Selected: {len(selected_communications)} communications\nIDs: {[c['name'] for c in selected_communications]}",
				"Transfer: Selected Communications"
			)
		else:
			selected_communications = all_communications
			frappe.log_error(
				f"No filter - using all {len(all_communications)} communications",
				"Transfer: Using All Communications"
			)
		
		# Create transfer notes
		transfer_notes = create_transfer_notes(ticket, selected_communications, all_communications)
		
		# Create CRM Lead with field mapping and fallbacks
		lead = frappe.new_doc("CRM Lead")
		if first_name:
			lead.first_name = first_name
		if last_name:
			lead.last_name = last_name
		
		# Email fallback: email -> email_id
		if customer_email:
			# Try email field first
			try:
				lead.email = customer_email
			except:
				# Fallback to email_id
				lead.email_id = customer_email
		
		# Phone fallback: mobile_no -> phone
		if customer_phone:
			# Try mobile_no field first
			try:
				lead.mobile_no = customer_phone
			except:
				# Fallback to phone
				lead.phone = customer_phone
		
		lead.status = "New"
		
		# Copy custom_reply_email_alias if it exists on the Ticket
		if ticket.get("custom_reply_email_alias"):
			lead.custom_reply_email_alias = ticket.custom_reply_email_alias
		
		# Set source - create "Support Transfer" if it doesn't exist
		source_name = "Support Transfer"
		if not frappe.db.exists("CRM Lead Source", source_name):
			try:
				frappe.get_doc({
					"doctype": "CRM Lead Source",
					"source_name": source_name,
				}).insert(ignore_permissions=True)
			except Exception as e:
				frappe.log_error(f"Error creating CRM Lead Source '{source_name}': {str(e)}")
				# Continue without source if creation fails
				source_name = None
		
		if source_name:
			lead.source = source_name
		
		lead.notes = transfer_notes
		lead.insert(ignore_permissions=True)
		
		# CRITICAL: Commit the lead before copying communications
		# Otherwise the communications can't reference a non-existent lead
		frappe.db.commit()
		
		frappe.log_error(
			f"Created CRM Lead: {lead.name}\nAbout to copy {len(selected_communications)} communications",
			"Transfer: Lead Created"
		)
		
		# Copy selected communications
		transferred_count = 0
		failed_count = 0
		
		if not selected_communications:
			frappe.log_error(
				f"WARNING: No communications to transfer for ticket {ticket_name}!\nAll comms: {len(all_communications)}\ncomm_ids param: {communication_ids}",
				"Transfer: No Communications!"
			)
		
		for idx, comm in enumerate(selected_communications, 1):
			try:
				frappe.log_error(
					f"Copying {idx}/{len(selected_communications)}: {comm['name']}\nSubject: {comm.get('subject', 'No Subject')[:50]}\nHas content: {bool(comm.get('content'))}\nHas text: {bool(comm.get('text_content'))}",
					f"Transfer: Copy Comm {idx}"
				)
				
				# Copy the communication - copy_communication will reload it
				copy_communication(comm["name"], "CRM Lead", lead.name)
				transferred_count += 1
				
				# Commit after each communication to ensure it's saved
				frappe.db.commit()
				
				frappe.log_error(
					f"Successfully copied {comm['name']} ({idx}/{len(selected_communications)})",
					f"Transfer: Copy Success {idx}"
				)
			except Exception as e:
				failed_count += 1
				error_msg = f"Error copying communication {comm['name']} to Lead {lead.name}:\nError: {str(e)}\n\nTraceback:\n{frappe.get_traceback()}"
				frappe.log_error(error_msg, f"Transfer: Copy Failed {idx}")
				# Continue with next communication instead of stopping
				continue
		
		frappe.log_error(
			f"Transfer complete\nSuccess: {transferred_count}\nFailed: {failed_count}\nTotal attempted: {len(selected_communications)}",
			"Transfer: Copy Summary"
		)
		
		# Delete source Ticket if requested
		if delete_source:
			try:
				frappe.delete_doc("HD Ticket", ticket_name, ignore_permissions=True, force=True)
			except Exception as e:
				frappe.log_error(f"Error deleting source ticket {ticket_name}: {str(e)}")
		
		# Return success response
		lead_url = get_url(f"/app/lead/{lead.name}")
		
		return {
			"success": True,
			"lead_name": lead.name,
			"lead_url": lead_url,
			"transferred_count": transferred_count,
			"message": _("Successfully transferred {0} email(s) to CRM Lead {1}").format(
				transferred_count, lead.name
			),
		}
		
	except Exception as e:
		frappe.log_error(f"Error in transfer_to_crm: {str(e)}")
		frappe.throw(_("Error transferring to CRM: {0}").format(str(e)))

