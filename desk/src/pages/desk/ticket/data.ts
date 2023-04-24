import { computed, ref, Ref, reactive } from "vue";
import { createDocumentResource } from "frappe-ui";

export let ticket = null;
export const contactId = computed(() => ticket?.doc?.contact);
export const ticketId: Ref<number> = ref(null);

export const sidebar = reactive({
	isVisible: true,
});

export const responseEditor = reactive({
	isExpanded: true,
	content: "",
	attachments: [],
});

/**
 * Initialize necessary data, to be shared across components. This contains
 * only shareable data. Individual sources are defined and used in respective
 * components.
 */
export async function init(id: number) {
	ticketId.value = id;

	ticket = createDocumentResource({
		doctype: "HD Ticket",
		fields: ["name", "custom_fields"],
		name: id,
		auto: true,
		whitelistedMethods: {
			getComments: "get_comments",
			getCommunications: "get_communications",
			replyViaAgent: {
				method: "reply_via_agent",
				onSuccess() {
					responseEditor.content = "";
					responseEditor.isExpanded = false;
				},
			},
		},
	});

	await ticket.get.promise;
}
