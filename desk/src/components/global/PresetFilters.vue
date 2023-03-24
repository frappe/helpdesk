<template>
	<Dropdown placement="left" :options="options">
		<template #default="{ toggleDropdown }">
			<div
				class="flex select-none flex-row items-center space-x-1"
				:class="{ 'cursor-pointer': !$_.isEmpty(options) }"
				@click="toggleDropdown"
			>
				<div class="text-lg font-semibold">
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
			default: "Ticket",
		},
		listTitle: {
			type: String,
			required: true,
			default: "Default List Title",
		},
		itemCount: {
			type: Number,
			required: true,
			default: 444,
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

		return {
			manager,
			// renderOptions,
			// route,
			user,
			// title,
			listFilters,
			presetFilters,
		};
	},
	computed: {
		title() {
			return `${this.listTitle} (${this.itemCount})`;
		},
		filters() {
			return this.manager.sudoFilters;
		},
		options() {
			let options = [];
			let data = this.$resources.presetFilterOptions.data || [];
			if (Object.keys(data).length) {
				Object.keys(data).forEach((group) => {
					if (data[group].length) {
						options.push({
							group: group === "user" ? "My Filters" : "Global",
							hideLabel: group !== "user",
							items: data[group].map((item) => {
								return {
									label: item.title,
									handler: () => {
										const q = this.listFilters.toQuery(item.filters);
										this.$router.push({ query: { q } });
										// debugger;
										// this.title = item.title;
										// this.presetFilters = [...item.filters];
										// this.manager.addFilters(
										// 	[...item.filters],
										// 	this.manager.options.urlQueryFilters
										// );
									},
									// filters: [...item.filters],
								};
							}),
						});
					}
				});
			}
			this.$nextTick(() => {
				this.sync();
			});
			return options;
		},
	},
	// watch: {
		// filters() {
		// 	this.sync();
		// },
	// },
	mounted() {
		// NOTE: probably need to change event
		// this.$socket.on("list_update", (data) => {
		// 	if (data.doctype === "FD Preset Filter") {
		// 		this.$resources.presetFilterOptions.fetch();
		// 	}
		// });
	},
	methods: {
		sync() {
			let filters = this.filters.filter((filter) => {
				return filter.fieldname && filter.filter_type && filter.value;
			});

			let checkIfFiltersAreSame = (a, b) => {
				if (a.length !== b.length) {
					return false;
				}
				for (let i = 0; i < a.length; i++) {
					if (a[i].fieldname !== b[i].fieldname) {
						return false;
					}
					if (
						a[i].fieldname === "_assign" &&
						a[i].value === "@me" &&
						b[i].value === this.user.user
					) {
						continue;
					}
					if (a[i].filter_type !== b[i].filter_type) {
						return false;
					}
					if (a[i].value !== b[i].value) {
						return false;
					}
				}
				return true;
			};

			this.title = `Filtered ${this.manager.options.doctype}s`;

			if (filters.length == 0) {
				this.title = `All ${this.manager.options.doctype}s`;
			} else {
				this.options.forEach((group) => {
					group.items.forEach((x) => {
						if (checkIfFiltersAreSame(x.filters, filters)) {
							this.title = x.label;
						}
					});
				});
			}
		},
	},
	resources: {
		presetFilterOptions() {
			return {
				url: "frappedesk.api.general.get_preset_filters",
				params: {
					doctype: this.doctype,
				},
				auto: true,
			};
		},
	},
};
</script>
