import { computed, ref, Ref, reactive } from "vue";
import { createDocumentResource } from "frappe-ui";

export const ticket__ = ref(null);
export const ticket = computed(() => ticket__.value);
export const contact = computed(() => ticket.value?.doc?.contact);
export const ticketId: Ref<number> = ref(null);

export const sidebar = reactive({
	isVisible: true,
});

/**
 * Initialize necessary data, to be shared across components. This contains
 * only shareable data. Individual data sources are defined and used in
 * respective components.
 */
export function init(id: number) {
	ticketId.value = id;

	ticket__.value = createDocumentResource({
		doctype: "HD Ticket",
		fields: ["name", "custom_fields"],
		name: id,
		auto: true,
	});
}
