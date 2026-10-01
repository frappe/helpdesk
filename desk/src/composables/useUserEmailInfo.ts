import { createResource } from "frappe-ui";

export function getUserEmailInfo() {
	return createResource({
		url: "helpdesk.api.auth.get_current_user_email_info",
		cache: "current-user-email-info",
		auto: true,
	});
}
