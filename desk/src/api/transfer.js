import { call } from "frappe-ui"
import { toast } from "frappe-ui"

/**
 * Get communications for transfer
 * @param {string} doctype - Document type (e.g., "HD Ticket")
 * @param {string} name - Document name
 * @returns {Promise<Array>} Array of communication records
 */
export async function getCommunicationsForTransfer(doctype, name) {
	try {
		console.log('[transfer.js] Getting communications for:', doctype, name);
		const result = await call("helpdesk.api.email_transfer.get_communications_for_transfer", {
			doctype,
			name,
		})
		console.log('[transfer.js] Got communications:', result?.length || 0, result);
		return result || []
	} catch (error) {
		console.error("Error fetching communications:", error)
		toast.error(error.messages?.[0] || "Error fetching communications")
		throw error
	}
}

/**
 * Transfer HD Ticket to CRM Lead
 * @param {string} ticketName - Ticket document name
 * @param {Array<string>} communicationIds - Array of communication IDs to transfer
 * @param {boolean} deleteSource - Whether to delete source ticket (default: true)
 * @returns {Promise<Object>} Transfer result with lead_name, lead_url, etc.
 */
export async function transferToCRM(ticketName, communicationIds = [], deleteSource = true) {
	try {
		console.log('[transfer.js] Transferring to CRM:', {
			ticketName,
			communicationIds,
			communicationIdsCount: communicationIds?.length || 0,
			deleteSource
		});
		
		const result = await call("helpdesk.api.email_transfer.transfer_to_crm", {
			ticket_name: ticketName,
			communication_ids: communicationIds,
			delete_source: deleteSource,
		})
		
		console.log('[transfer.js] Transfer result:', result);
		
		if (result.success) {
			toast.success(result.message || "Successfully transferred to CRM Lead")
			return result
		} else {
			throw new Error(result.message || "Transfer failed")
		}
	} catch (error) {
		console.error("Error transferring to CRM:", error)
		toast.error(error.messages?.[0] || error.message || "Error transferring to CRM")
		throw error
	}
}

