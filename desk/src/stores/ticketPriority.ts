import { ref, Ref } from "vue";
import { defineStore } from "pinia";
import { createListResource } from "frappe-ui";

type TicketPriority = {
	name: string;
	description: string;
};

export const useTicketPriorityStore = defineStore("ticketPriority", () => {
	const options: Ref<Array<TicketPriority>> = ref([]);

	createListResource({
		doctype: "HD Ticket Priority",
		auto: true,
		onSuccess(data: Array<TicketPriority>) {
			options.value = data;
		},
	});

	function getAll(): Array<TicketPriority> {
		return options.value;
	}

	function getNames(): Array<string> {
		return options.value.map((o) => o.name);
	}

	return {
		getAll,
		getNames,
	};
});
