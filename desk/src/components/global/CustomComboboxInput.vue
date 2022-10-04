<template>
	<div class="relative inline-block text-left">
		<Combobox v-model="selectedItem">
			<ComboboxInput
				class="rounded-md w-full border-none focus:ring-0 py-2 pl-3 pr-10 text-sm leading-5 text-gray-900 bg-slate-100"
				autocomplete="off"
				@change="query = $event.target.value"
			/>
			<ComboboxOptions
				class="absolute z-10 mt-2 bg-white divide-y divide-gray-100 rounded-md shadow-lg min-w-40 ring-1 ring-black ring-opacity-5 focus:outline-none"
			>
				<div
					v-if="filteredItems.length === 0 && query !== ''"
					class="select-none relative py-2 px-4 text-gray-700"
				>
					No Results Found
				</div>
				<ComboboxOption
					v-slot="{ selected, active }"
					v-for="item in filteredItems"
					:key="item"
					:value="item"
				>
					<li
						class="cursor-default select-none relative py-2 pl-4 pr-4 text-gray-900"
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
</template>

<script>
import {
	Combobox,
	ComboboxOptions,
	ComboboxOption,
	ComboboxInput,
} from "@headlessui/vue"
import { ref } from "vue"

export default {
	name: "CustomComboboxInput",
	props: ["options", "value"],
	components: {
		Combobox,
		ComboboxOptions,
		ComboboxOption,
		ComboboxInput,
	},
	setup() {
		const selectedItem = ref(null)
		const query = ref(null)

		return {
			selectedItem,
			query,
		}
	},
	computed: {
		filteredItems() {
			return this.query === ""
				? this.options
				: this.options.filter((item) => {
						return item
							.toLowerCase()
							.includes(this.query.toLowerCase())
				  })
		},
	},
}
</script>
