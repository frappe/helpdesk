import { ref } from "vue";
import { defineStore } from "pinia";

export const useTicketStatusStore = defineStore("ticketStatus", () => {
	const options = ref(["Open", "Replied", "Resolved", "Closed"]);

	return {
		options,
	};
});
