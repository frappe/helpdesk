import { computed, ComputedRef } from "vue";
import { defineStore } from "pinia";
import { createListResource } from "frappe-ui";

type Agent = {
	name: string;
	agent_name: string;
	is_active: boolean;
};

export const useAgentStore = defineStore("agent", () => {
	const d__ = createListResource({
		doctype: "HD Agent",
		fields: ["*"],
		auto: true,
	});

	const options: ComputedRef<Array<Agent>> = computed(
		() => d__.list?.data || []
	);

	return {
		options,
	};
});
