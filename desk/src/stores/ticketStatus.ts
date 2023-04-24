import { computed, ref } from "vue";
import { defineStore } from "pinia";

export const useTicketStatusStore = defineStore("ticketStatus", () => {
	const options = ref(["Open", "Replied", "Resolved", "Closed"]);
	const dropdown = computed(() =>
		options.value.map((o) => ({
			label: o,
			value: o,
		}))
	);

	return {
		dropdown,
		options,
	};
});
