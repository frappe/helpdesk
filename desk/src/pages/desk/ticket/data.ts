import { reactive } from "vue";
import { defineStore } from "pinia";
import { createDocumentResource } from "frappe-ui";
import { socket } from "@/socket";
import { createToast } from "@/utils/toasts";

export const useTicketStore = defineStore("ticket", () => {
	const sidebar = reactive({
		isExpanded: true,
	});

	const editor = reactive({
		isExpanded: false,
		content: "",
		attachments: [],
		cc: [],
		bcc: [],
		isCcVisible: false,
		isBccVisible: false,
		tiptap: null,
	});

	const ticket = createDocumentResource({
		doctype: "HD Ticket",
		fields: ["name", "custom_fields"],
		name: 747,
		auto: false,
		whitelistedMethods: {
			markSeen: "mark_seen",
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
				debounce: 500,
				onSuccess() {
					clean();
				},
				validate() {
					if (editor.tiptap?.isEmpty) {
						return "Message is empty";
					}
				},
				onError(error) {
					createToast({
						title: error.message,
						text: error.messages?.join("\n"),
						icon: "x",
						iconClasses: "text-red-500",
					});
				},
			},
		},
	});

	/**
	 * Initialize necessary data, to be shared across components. This contains
	 * only shareable data. Individual sources are defined and used in respective
	 * components.
	 */
	async function init(name: number) {
		ticket.name = name;
		ticket.reload();
		await ticket.get.promise;
		startListening();
	}

	/**
	 * Reset all states, and stop listening to socket events
	 */
	function deinit() {
		clean();
		endListening();
	}

	function startListening() {
		socket.on("helpdesk:ticket-update", (data) => {
			if (parseInt(data.name) === ticket.doc.name) ticket.reload();
		});

		socket.on("helpdesk:ticket-assignee-update", (data) => {
			if (parseInt(data.name) === ticket.doc.name) ticket.getAssignees.reload();
		});
	}

	function endListening() {
		socket.off("helpdesk:ticket-update");
		socket.off("helpdesk:ticket-assignee-update");
	}

	function clean() {
		editor.isExpanded = false;
		editor.content = "";
		editor.attachments = [];
		editor.cc = [];
		editor.bcc = [];
		editor.isCcVisible = false;
		editor.isBccVisible = false;
		sidebar.isExpanded = true;
	}

	return {
		clean,
		deinit,
		editor,
		init,
		sidebar,
		ticket,
	};
});
