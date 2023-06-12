<template>
	<div class="flex flex-row items-center space-x-1 text-base select-none">
		<div v-for="filter in filters" :key="filter">
			<FilterBoxItem
				:ref="`filter-box-item-${filter.fieldname}`"
				:filter="filter"
				@add-filter="applyFilters"
				@remove-filter="
					() => {
						manager.sudoFilters.splice(
							manager.sudoFilters.indexOf(filter),
							1
						)
						applyFilters()
					}
				"
			/>
		</div>
		<Dropdown
			:options="filterBoxFieldnameOptions"
			v-if="showAddFilterButton"
		>
			<template v-slot="{ toggle }">
				<div
					role="button"
					class="flex flex-row space-x-1 items-center px-1.5 py-0.5 rounded border border-dashed border-gray-500 text-gray-600 hover:text-gray-900 hover:bg-gray-100"
					@click="toggle"
				>
					<FeatherIcon name="plus" class="h-4 w-4" />
					<div>Filter</div>
				</div>
			</template>
		</Dropdown>
	</div>
</template>

<script>
import { FeatherIcon, Dropdown } from "frappe-ui"
import FilterBoxItem from "@/components/global/FilterBoxItem.vue"

export default {
	name: "FilterBox",
	components: {
		FeatherIcon,
		Dropdown,
		FilterBoxItem,
	},
	inject: ["manager", "renderOptions"],
	computed: {
		showAddFilterButton() {
			return (
				this.manager.sudoFilters.filter((filter) => {
					if (["like", "not like"].includes(filter.filter_type)) {
						return !(filter.fieldname && filter.filter_type)
					}
					return !(
						filter.fieldname &&
						filter.filter_type &&
						filter.value
					)
				}).length === 0
			)
		},
		filters() {
			return this.manager.sudoFilters
		},
		filterBoxFieldnameOptions() {
			// TODO: redo the fields list to options part
			let options = []

			for (let i in this.manager.options.fields) {
				let fieldname = this.manager.options.fields[i]

				let label =
					this.manager.helperMethods.convertFieldNameToLabel(
						fieldname
					)
				if (
					label && // monkey-patch to remove _seen from the list
					!this.manager.sudoFilters.find(
						(f) => f.fieldname === fieldname
					) // don't show filter options that are already applied
				) {
					options.push({
						label,
						onClick: () => {
							this.createNewFilterItem(fieldname, label)
						},
					})
				}
			}
			return options
		},
	},
	methods: {
		createNewFilterItem(fieldname, label = "") {
			this.manager.sudoFilters.push({
				label: label || fieldname,
				data_type: null,
				fieldname: fieldname,
				filter_type: "",
				value: "",
			})
		},
		applyFilters() {
			let filters = this.manager.sudoFilters.filter((f) => {
				if (["like", "not like"].includes(f.filter_type)) {
					return f.fieldname && f.filter_type
				}
				return f.fieldname && f.filter_type && f.value
			})
			this.manager.addFilters(
				filters,
				this.manager.options.urlQueryFilters
			)
		},
	},
}
</script>
