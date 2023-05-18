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
		pageLength: 99999,
	});

	const options: ComputedRef<Array<Agent>> = computed(
		() => d__.list?.data || []
	);
	const dropdown = computed(() =>
		options.value.map((o) => ({
			label: o.agent_name,
			value: o.name,
		}))
	);

	return {
		dropdown,
		options,
	};
});
