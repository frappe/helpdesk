<template>
	<Dropdown placement="left" :options="options">
		<template v-slot="{ toggleDropdown }">
			<div
				class="flex flex-row items-center space-x-1 cursor-pointer select-none"
				@click="toggleDropdown"
			>
				<div class="text-lg font-semibold">
					{{
						`All ${manager.options.doctype}s (${manager.totalCount})`
					}}
				</div>
				<FeatherIcon name="chevron-down" class="h-4 w-4 stroke-2" />
			</div>
		</template>
	</Dropdown>
</template>

<script>
import { Dropdown, FeatherIcon } from "frappe-ui"

export default {
	name: "PresetFilters",
	components: {
		Dropdown,
		FeatherIcon,
	},
	inject: ["manager", "user"],
	computed: {
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
										this.$emit("apply-filter", item.filters)
									},
								}
							}),
						})
					}
				})
			}
			return options
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
