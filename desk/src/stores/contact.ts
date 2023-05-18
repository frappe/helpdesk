import { computed, ComputedRef } from "vue";
import { defineStore } from "pinia";
import { createListResource } from "frappe-ui";

type Contact = {
	name: string;
	first_name: string;
	last_name: string;
	full_name: string;
	email_id: string;
};

export const useContactStore = defineStore("contact", () => {
	const d__ = createListResource({
		doctype: "Contact",
		fields: ["*"],
		auto: true,
		pageLength: 99999,
	});

	const options: ComputedRef<Array<Contact>> = computed(
		() => d__.list?.data || []
	);

	return {
		options,
	};
});
