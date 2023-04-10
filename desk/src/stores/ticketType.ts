import { computed, ComputedRef } from "vue";
import { defineStore } from "pinia";
import { createListResource } from "frappe-ui";

type TicketType = {
	name: string;
	description: string;
	priority: string;
};

export const useTicketTypeStore = defineStore("ticketType", () => {
	const d__ = createListResource({
		doctype: "HD Ticket Type",
		fields: ["*"],
		auto: true,
	});

	const options: ComputedRef<Array<TicketType>> = computed(
		() => d__.list?.data || []
	);

	return {
		options,
	};
});
