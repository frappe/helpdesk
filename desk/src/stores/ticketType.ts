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
		pageLength: 99999,
	});

	const options: ComputedRef<Array<TicketType>> = computed(
		() => d__.list?.data || []
	);
	const dropdown = computed(() =>
		options.value.map((o) => ({
			label: o.name,
			value: o.name,
		}))
	);

	return {
		dropdown,
		options,
	};
});
