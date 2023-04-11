<template>
	<Dropdown
		:options="options"
		:button="{
			label: title,
			'icon-right': 'chevron-down',
		}"
	/>
</template>

<script>
import { ref } from "vue";
import { Dropdown } from "frappe-ui";
import { useListFilters } from "@/composables/listFilters";

export default {
	name: "PresetFilters",
	components: {
		Dropdown,
	},
	setup() {
		const listFilters = useListFilters();
		const presetFilters = ref([]);
		const presetTitle = ref("");

		return {
			listFilters,
			presetFilters,
			presetTitle,
		};
	},
	computed: {
		currentQuery() {
			return this.$route.query.q;
		},
		title() {
			if (this.presetTitle) return this.presetTitle;
			if (this.currentQuery) return "Filtered Tickets";
			return "All Tickets";
		},
		presets() {
			return this.$resources.presetFilterOptions.data || [];
		},
		options() {
			let options = [];
			let data = this.presets;
			if (Object.keys(data).length) {
				Object.keys(data).forEach((group) => {
					if (data[group].length) {
						options.push({
							group: group === "user" ? "My Filters" : "Global",
							hideLabel: group !== "user",
							items: data[group].map((item) => {
								const q = this.listFilters.toQuery(item.filters);

								if (q === this.currentQuery) {
									this.presetTitle = item.title;
								}

								return {
									label: item.title,
									handler: () => {
										this.listFilters.applyQuery(q);
									},
								};
							}),
						});
					}
				});
			}

			return options;
		},
	},
	mounted() {
		this.$socket.on("helpdesk:new-preset-filter", (data) => {
			if (data.reference_doctype !== "HD Ticket") return;
			this.$resources.presetFilterOptions.reload();
		});
	},
	unmounted() {
		this.$socket.off("helpdesk:new-preset-filter");
	},
	resources: {
		presetFilterOptions() {
			return {
				url: "helpdesk.api.general.get_preset_filters",
				params: {
					doctype: "HD Ticket",
				},
				cache: ["Preset Filter", this.doctype],
				auto: true,
			};
		},
	},
};
</script>
