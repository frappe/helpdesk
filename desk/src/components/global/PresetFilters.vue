<template>
	<Dropdown placement="left" :options="options">
		<template #default="{ toggleDropdown }">
			<div
				class="flex select-none flex-row items-center space-x-1"
				:class="{ 'cursor-pointer': options.length > 0 }"
				@click="toggleDropdown"
			>
				<div class="text-lg font-semibold">
					{{ `${ListTitle ? ListTitle : title} (${manager.totalCount})` }}
				</div>
				<FeatherIcon
					v-if="options.length > 0"
					name="chevron-down"
					class="h-4 w-4 stroke-2"
				/>
			</div>
		</template>
	</Dropdown>
</template>

<script>
import { Dropdown, FeatherIcon } from "frappe-ui";
import { inject, ref } from "vue";

export default {
	name: "PresetFilters",
	components: {
		Dropdown,
		FeatherIcon,
	},
	props: ["ListTitle"],
	setup() {
		const manager = inject("manager");
		const presetFilters = ref([]);
		const renderOptions = inject("renderOptions");
		const title = ref(`All ${manager.value.options.doctype}s`);
		const user = inject("user");

		return {
			manager,
			presetFilters,
			renderOptions,
			title,
			user,
		};
	},
	computed: {
		filters() {
			return this.manager.sudoFilters;
		},
		options() {
			const data = this.$resources.presetFilterOptions.data || {};
			const d = Object.keys(data);

			this.$nextTick(() => {
				this.sync();
			});

			return d
				.filter((group) => data[group].length)
				.map((group) => ({
					group: group === "user" ? "My Filters" : "Global",
					hideLabel: group !== "user",
					items: data[group].map((item) => ({
						label: item.title,
						handler: () => {
							this.title = item.title;
							this.presetFilters = [...item.filters];
							this.manager.addFilters(
								[...item.filters],
								this.manager.options.urlQueryFilters
							);
						},
						filters: [...item.filters],
					})),
				}));
		},
	},
	watch: {
		filters() {
			this.sync();
		},
	},
	mounted() {
		this.$socket.on("list_update", (data) => {
			if (data.doctype === "FD Preset Filter") {
				this.$resources.presetFilterOptions.fetch();
			}
		});
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
				method: "frappedesk.api.general.get_preset_filters",
				params: {
					doctype: this.manager.options.doctype,
				},
				auto: true,
			};
		},
	},
};
</script>
