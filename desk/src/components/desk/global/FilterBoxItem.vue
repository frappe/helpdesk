<template>
	<div class="flex space-x-2 items-center">
		<div class="w-2/5">
			<Dropdown
				class="w-full"
				placement="left"
				:options="getDropdownOptions(index)"
			>
				<template v-slot="{ toggleDropdown }">
					<div class="w-full cursor-pointer" @click="toggleDropdown">
						<div
							class="w-full py-1 px-2 bg-gray-100 rounded flex items-center"
						>
							<div class="grow">
								{{
									getOption(
										Object.keys(modelValue[filterIndex])[0]
									).label
								}}
							</div>
							<CustomIcons name="select" class="w-4 h-4" />
						</div>
					</div>
				</template>
			</Dropdown>
		</div>
		<div
			class="w-3/5"
			v-if="getOption(Object.keys(modelValue[filterIndex])[0])"
		>
			<div
				v-if="
					getOption(Object.keys(modelValue[filterIndex])[0]).type ==
					'combobox'
				"
			>
				<Combobox v-model="selctedFilterValue">
					<ComboboxInput
						class="rounded-md w-full py-1 border-none focus:ring-0 pl-3 pr-10 text-sm leading-5 text-gray-900 bg-gray-100"
						autocomplete="off"
						@change="query = $event.target.value"
					/>
					<ComboboxOptions
						class="absolute z-50 mt-1 overflow-auto text-base bg-white rounded-md shadow-lg max-h-40 ring-1 ring-black ring-opacity-5 focus:outline-none sm:text-sm"
					>
						<div
							v-if="filterItems.length === 0 && query !== ''"
							class="select-none py-2 relative px-4 text-slate-400"
						>
							Nothing found
						</div>
						<ComboboxOption
							v-slot="{ selected, active }"
							v-for="item in filterItems"
							:key="item"
							:value="item"
						>
							<li
								class="w-[158px] cursor-default select-none relative py-2 pl-4 pr-4 text-gray-900"
								:class="{ 'bg-slate-50': active }"
							>
								<span
									class="block truncate"
									:class="{
										'font-medium': selected,
										'font-normal': !selected,
									}"
								>
									{{ item }}
								</span>
							</li>
						</ComboboxOption>
					</ComboboxOptions>
				</Combobox>
			</div>
		</div>
		<FeatherIcon
			v-if="removable"
			name="x"
			class="w-4 h-4 cursor-pointer hover:stroke-red-500"
			@click="removeFilter()"
		/>
	</div>
</template>

<script>
import { FeatherIcon, Dropdown } from "frappe-ui"
import CustomIcons from "./CustomIcons.vue"
import { ref } from "vue"
import {
	Combobox,
	ComboboxInput,
	ComboboxOptions,
	ComboboxOption,
} from "@headlessui/vue"

export default {
	props: ["options", "modelValue", "filterIndex", "removable"], // modelValue: filter
	components: {
		FeatherIcon,
		Dropdown,
		CustomIcons,
		Combobox,
		ComboboxInput,
		ComboboxOptions,
		ComboboxOption,
	},
	setup() {
		const query = ref("")
		const filteredComboboxItems = ref([])
		const selctedFilterValue = ref("")

		return { query, filteredComboboxItems, selctedFilterValue }
	},
	mounted() {
		if (Object.values(this.modelValue).length > 0) {
			let filter = Object.values(this.modelValue)[this.filterIndex]
			this.selctedFilterValue = Object.values(filter)[0]
		}
	},
	computed: {
		filterItems() {
			if (
				this.options &&
				this.getOption(
					Object.keys(this.modelValue[this.filterIndex])[0]
				)
			) {
				let items = this.getOption(
					Object.keys(this.modelValue[this.filterIndex])[0]
				).items
				return this.query === ""
					? items
					: items.filter((item) => {
							return item
								? item
										.toLowerCase()
										.includes(this.query.toLowerCase())
								: null
					  })
			} else {
				return []
			}
		},
	},
	watch: {
		selctedFilterValue(newValue) {
			this.modelValue[this.filterIndex][
				Object.keys(this.modelValue[this.filterIndex])[0]
			] = newValue
		},
	},
	methods: {
		getDropdownOptions() {
			let items = []
			this.options.forEach((item, index) => {
				items.push({
					label: item.label,
					onClick: () => {
						this.modelValue[this.filterIndex] = {}
						this.modelValue[this.filterIndex][
							this.options[index].name
						] = ""
					},
				})
			})
			return items
		},
		getOption(name) {
			if (this.options) {
				let option = this.options.find((item) => item.name == name)
				if (!option.type) {
					option.type = "combobox"
				}
				return option
			} else {
				return null
			}
		},
		removeFilter() {
			delete this.modelValue[this.filterIndex]
		},
	},
}
</script>

<style></style>
