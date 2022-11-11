<template>
	<Dropdown placement="left" :options="options">
		<template v-slot="{ toggleDropdown }">
			<div
				class="flex flex-row items-center space-x-1 cursor-pointer select-none"
				@click="toggleDropdown"
			>
				<div class="text-lg font-semibold">
					{{ `${title} (${manager.totalCount})` }}
				</div>
				<FeatherIcon name="chevron-down" class="h-4 w-4 stroke-2" />
			</div>
		</template>
	</Dropdown>
</template>

<script>
import { Dropdown, FeatherIcon } from "frappe-ui"
import { inject, ref } from "vue"

export default {
	name: "PresetFilters",
	components: {
		Dropdown,
		FeatherIcon,
	},
	setup() {
		const manager = inject("manager")
		const renderOptions = inject("renderOptions")
		const user = inject("user")

		const title = ref(`All ${manager.value.options.doctype}s`)

		const presetFilters = ref([])

		return {
			manager,
			renderOptions,
			user,
			title,
			presetFilters,
		}
	},
	mounted() {
		this.$socket.on("list_update", (data) => {
			if (data.doctype === "FD Preset Filter") {
				this.$resources.presetFilterOptions.fetch().then(() => {
					this.sync()
				})
			}
		})
	},
	watch: {
		filters(val) {
			this.sync()
		},
	},
	computed: {
		filters() {
			return this.manager.sudoFilters
		},
		options() {
			let options = []
			let data = this.$resources.presetFilterOptions.data || []
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
										this.title = item.title
										this.presetFilters = [...item.filters]
										this.manager.addFilters(
											[...item.filters],
											this.renderOptions.urlQueryFilters
										)
									},
									filters: [...item.filters],
								}
							}),
						})
					}
				})
			}
			return options
		},
	},
	methods: {
		sync() {
			let filters = this.filters.filter((filter) => {
				return filter.fieldname && filter.filter_type && filter.value
			})

			let checkIfFiltersAreSame = (a, b) => {
				if (a.length !== b.length) {
					return false
				}
				for (let i = 0; i < a.length; i++) {
					if (a[i].fieldname !== b[i].fieldname) {
						return false
					}
					if (a[i].filter_type !== b[i].filter_type) {
						return false
					}
					if (a[i].value !== b[i].value) {
						return false
					}
				}
				return true
			}

			this.title = `Filtered ${this.manager.options.doctype}s`

			if (filters.length == 0) {
				this.title = `All ${this.manager.options.doctype}s`
			} else {
				this.options.forEach((group) => {
					group.items.forEach((x) => {
						if (checkIfFiltersAreSame(x.filters, filters)) {
							this.title = x.label
						}
					})
				})
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
			}
		},
	},
}
</script>
