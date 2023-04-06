import { computed, ComputedRef } from "vue";
import { defineStore } from "pinia";
import { createListResource } from "frappe-ui";

type TicketPriority = {
	name: string;
	description: string;
};

export const useTicketPriorityStore = defineStore("ticketPriority", () => {
	const d__ = createListResource({
		doctype: "HD Ticket Priority",
		auto: true,
	});

	const options: ComputedRef<Array<TicketPriority>> = computed(
		() => d__.list?.data || []
	);
	const names = computed(() => options.value.map((o) => o.name));

	return {
		options,
		names,
	};
});
