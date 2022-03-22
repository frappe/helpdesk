<template>
	<div class="absolute border rounded shadow-md p-5 bg-white z-50 w-[386px] ml-[10px] text-base">
		<div class="border-b pb-4 mb-4 space-y-2">
			<div v-for="(filter, index) in tempFilters" :key="index">
				<FilterBoxItem v-if="filter" click="w-full" :options="options" v-model="tempFilters" :filterIndex="index" :removable="tempFilters.filter((item) => item != null).length > 1"/>
			</div>
		</div>
		<div class="flex items-center text-gray-500">
			<div class="flex items-center space-x-2 hover:text-gray-600 cursor-pointer">
				<FeatherIcon name="plus" class="w-4 h-4" />
				<div @click="addFilter()">Add a Filter</div>
			</div>
			<div class="grow"></div>
			<div>
				<div class="flex flex-reverse space-x-2">
					<Button appearance="primary" @click="applyFilters()">Apply Filters</Button>
					<Button appearance="secondary" @click="clearAllFilters()">Clear All</Button>
				</div>
			</div>
		</div>
	</div>
</template>

<script>
import { FeatherIcon, Dropdown } from 'frappe-ui'
import { inject, ref } from 'vue'
import CustomIcons from './CustomIcons.vue'
import FilterBoxItem from './FilterBoxItem.vue'
import { Combobox, ComboboxInput, ComboboxOptions, ComboboxOption } from '@headlessui/vue'

export default {
	name: 'FilterBox',
	props: {
		options: {type: [Array]},
		modelValue: {type: [Array]},
		prevFilters: {type: [Array]}
	},
	components: {
		FeatherIcon,
		Dropdown,
		CustomIcons,
		FilterBoxItem,
		Combobox,
		ComboboxInput,
		ComboboxOptions,
		ComboboxOption
	},
	setup() {
		const ticketFilter = inject('ticketFilter')
		const tempFilters = ref([])	//TODO: use this list to create the final filters when apply is triggered
		const query = ref({})

		return { ticketFilter, tempFilters, query }
	},
	mounted() {
	},
	methods: {
		addFilter() {
			let newItem = {}
			newItem[this.options[0].name] = ''
			this.tempFilters.push(newItem)
		},
		applyFilters() {
			this.$emit("update:modelValue", this.tempFilters.filter((item) => item != null && Object.values(item)[0] != ''));
		},
		clearAllFilters() {
			this.tempFilters = []
			this.applyFilters()
			this.addFilter()
		}
	}
}
</script>