<template>
	<div class="flex flex-row items-center space-x-1 text-base select-none">
		<div v-for="filter in filters" :key="filter">
			<FilterBoxItem
				:ref="`filter-box-item-${filter.fieldname}`"
				:filter="filter"
				@apply-filter="applyFilter"
			/>
		</div>
		<Dropdown :options="filterBoxFieldnameOptions">
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
import { ref } from "vue"

export default {
	name: "FilterBox",
	components: {
		FeatherIcon,
		Dropdown,
		FilterBoxItem,
	},
	inject: ["manager"],
	setup() {
		const filters = ref([])
		return {
			filters,
		}
	},
	data() {
		return {
			isMounted: false,
		}
	},
	mounted() {
		this.isMounted = true
	},
	computed: {
		filterBoxFieldnameOptions() {
			// TODO: redo the fields list to options part
			let options = []

			for (let i in this.manager.options.fields) {
				let fieldname = this.manager.options.fields[i]

				let convertFieldNameToLabel = (fieldname) => {
					switch (fieldname) {
						case "_assign":
							return "Assigned to"
						case "_seen":
							return false
						default:
							fieldname = fieldname.replace(/_/g, " ")
							return (
								fieldname.charAt(0).toUpperCase() +
								fieldname.slice(1)
							)
					}
				}

				let label = convertFieldNameToLabel(fieldname)
				if (
					label && // monkey-patch to remove _seen from the list
					!this.filters.find((f) => f.fieldname === fieldname) // don't show filter options that are already applied
				) {
					options.push({
						label,
						handler: () => {
							this.addFilter(fieldname, label)
						},
					})
				}
			}
			return options
		},
	},
	methods: {
		addFilter(fieldname, label = "") {
			this.filters.push({
				label: label || fieldname,
				fieldname: fieldname,
				filter_type: "",
				value: "",
			})
		},
		applyFilter(filter) {
			this.manager.addFilter(filter, true)
		},
	},
}
</script>
