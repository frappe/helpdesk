import { reactive } from "vue";
import { createDocumentResource } from "frappe-ui";
import { socket } from "@/socket";

export let ticket = null;

export const sidebar = reactive({
	isVisible: true,
});

export const editor = reactive({
	isExpanded: false,
	content: "",
	attachments: [],
	cc: [],
	bcc: [],
	isCcVisible: false,
	isBccVisible: false,
});

/**
 * Initialize necessary data, to be shared across components. This contains
 * only shareable data. Individual sources are defined and used in respective
 * components.
 */
export async function init(id: number) {
	ticket = createDocumentResource({
		doctype: "HD Ticket",
		fields: ["name", "custom_fields"],
		name: id,
		auto: true,
		whitelistedMethods: {
			assign: "assign_agent",
			getAssignees: "get_assignees",
			getComments: "get_comments",
			getCommunications: "get_communications",
			getLastCommunication: {
				method: "get_last_communication",
				auto: true,
				onSuccess(data: { cc: string; bcc: string }) {
					data?.cc?.split(",").forEach((recipent) => editor.cc.push(recipent));

					data?.bcc
						?.split(",")
						.forEach((recipent) => editor.bcc.push(recipent));
				},
			},
			replyViaAgent: {
				method: "reply_via_agent",
				onSuccess() {
					clean();
				},
			},
		},
	});

	await ticket.get.promise;

	socket.on("helpdesk:ticket-update", (data) => {
		if (parseInt(data.name) == ticket.doc.name) ticket.reload();
	});

	socket.on("helpdesk:ticket-assignee-update", (data) => {
		if (parseInt(data.name) == ticket.doc.name) ticket.getAssignees.reload();
	});
}

export function clean() {
	editor.isExpanded = false;
	editor.content = "";
	editor.attachments = [];
	editor.cc = [];
	editor.bcc = [];
	editor.isCcVisible = false;
	editor.isBccVisible = false;

	socket.off("helpdesk:ticket-update");
	socket.off("helpdesk:ticket-assignee-update");
}
