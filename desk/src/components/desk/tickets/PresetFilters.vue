<template>
	<Dropdown placement="left" :options="options">
		<template #default="{ toggleDropdown }">
			<div
				class="flex select-none items-center gap-2 border px-2 py-1 rounded-lg border-gray-300"
				:class="{ 'cursor-pointer': !$_.isEmpty(options) }"
				@click="toggleDropdown"
			>
				<div class="text-base">
					{{ title }}
				</div>
				<FeatherIcon
					v-if="!$_.isEmpty(options)"
					name="chevron-down"
					class="h-4 w-4 stroke-2"
				/>
			</div>
		</template>
	</Dropdown>
</template>

<script>
import { inject, ref } from "vue";
import { Dropdown, FeatherIcon } from "frappe-ui";
import { useListFilters } from "@/composables/listFilters"

export default {
	name: "PresetFilters",
	components: {
		Dropdown,
		FeatherIcon,
	},
	props: {
		doctype: {
			type: String,
			required: true,
		},
		listTitle: {
			type: String,
			required: true,
			default: "Default List Title",
		},
	},
	setup() {
		const manager = inject("manager");
		// const renderOptions = inject("renderOptions");
		const user = inject("user");

		// const title = ref(`All ${manager.value.options.doctype}s`);

		// const route = useRoute();

		const listFilters = useListFilters();
		const presetFilters = ref([]);

		const presetTitle = ref("");

		return {
			manager,
			// renderOptions,
			// route,
			user,
			// title,
			listFilters,
			presetFilters,
			presetTitle,
		};
	},
	computed: {
		title() {
			// return `${this.listTitle} (${this.itemCount})`;
			return this.presetTitle || "All tickets";
		},
		filters() {
			return this.manager.sudoFilters;
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

								if (q === this.$route.query.q) {
									this.presetTitle = item.title;
								}
							
								return {
									label: item.title,
									handler: () => {
										this.$router.push({ query: { q } });
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
		// NOTE: probably need to change event
		// this.$socket.on("list_update", (data) => {
		// 	if (data.doctype === "FD Preset Filter") {
		// 		this.$resources.presetFilterOptions.fetch();
		// 	}
		// });
	},
	resources: {
		presetFilterOptions() {
			return {
				url: "frappedesk.api.general.get_preset_filters",
				params: {
					doctype: this.doctype,
				},
				cache: ["Preset Filter", this.doctype],
				auto: true,
			};
		},
	},
};
</script>
