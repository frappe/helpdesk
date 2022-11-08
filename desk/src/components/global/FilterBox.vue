<template>
	<div class="flex flex-row items-center space-x-1 text-base">
		<div v-for="filter in filters" :key="filter">
			<FilterBoxItem :filter="filter" @apply-filter="applyFilter" />
		</div>
		<div
			role="button"
			class="flex flex-row space-x-1 items-center px-1.5 py-0.5 rounded border border-dashed border-gray-500 text-gray-600 hover:text-gray-900 hover:bg-gray-100"
			@click="addFilter"
		>
			<FeatherIcon name="plus" class="h-4 w-4" />
			<div>Filter</div>
		</div>
	</div>
</template>

<script>
import { FeatherIcon } from "frappe-ui"
import FilterBoxItem from "@/components/global/FilterBoxItem.vue"
import { ref } from "vue"

export default {
	name: "FilterBox",
	components: {
		FeatherIcon,
		FilterBoxItem,
	},
	inject: ["manager"],
	setup() {
		const filters = ref([])
		return {
			filters,
		}
	},
	methods: {
		addFilter() {
			this.filters.push({
				fieldname: "",
				operator: "",
				value: "",
			})
		},
		applyFilter(filter) {
			this.manager.addFilter(filter, true)
		},
	},
}
</script>
