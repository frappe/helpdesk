<template>
	<Combobox
		v-model="selectedValue"
		nullable
		v-slot="{ open: isComboboxOpen }"
	>
		<Popover class="w-full">
			<template #target="{ open: openPopover }">
				<div class="w-full">
					<slot name="input-holder" :open="foo">
						<ComboboxButton
							class="flex items-center justify-between w-full py-1.5 pl-3 pr-2 rounded-md bg-gray-100"
							:class="{ 'rounded-b-none': isComboboxOpen }"
							@click="
								() => {
									openPopover()
								}
							"
						>
							<slot
								name="input"
								:selectedValue="selectedValue"
								:placeholder="placeholder"
							>
								<span
									class="text-base truncate"
									v-if="selectedValue"
								>
									{{ displayValue(selectedValue) }}
								</span>
								<span class="text-base text-gray-500" v-else>
									{{ placeholder || "" }}
								</span>
							</slot>
							<CustomIcons
								name="select"
								class="w-[12px] h-[12px] stroke-gray-500"
							/>
						</ComboboxButton>
					</slot>
				</div>
			</template>
			<template #body>
				<ComboboxOptions
					class="px-1.5 pb-1.5 bg-white rounded-md shadow-md rounded-t-none max-h-[11rem] overflow-y-auto"
					static
					:class="width ? `w-[${width}px]` : 'w-[250px]'"
					v-show="isComboboxOpen"
				>
					<div
						class="flex items-st items-stretch space-x-1.5 sticky top-0 pt-1.5 mb-1.5 bg-white"
					>
						<ComboboxInput
							class="w-full placeholder-gray-500 form-input"
							type="text"
							@change="
								(e) => {
									query = e.target.value
								}
							"
							:value="query"
							autocomplete="off"
							placeholder="Search by keyword"
						/>
						<Button icon="x" @click="selectedValue = null" />
					</div>
					<ComboboxOption
						as="template"
						v-for="option in filteredOptions"
						:key="option.value"
						:value="option"
						v-slot="{ active, selected }"
					>
						<li
							:class="[
								'px-2.5 py-1.5 rounded-md text-base truncate',
								{ 'bg-gray-100': active },
							]"
						>
							{{ option.label }}
						</li>
					</ComboboxOption>
					<slot
						v-if="filteredOptions.length == 0"
						name="no-result-found"
					>
						<li
							class="px-2.5 py-1.5 rounded-md text-base text-gray-600"
						>
							No results found
						</li>
					</slot>
				</ComboboxOptions>
			</template>
		</Popover>
	</Combobox>
</template>
<script>
import {
	Combobox,
	ComboboxInput,
	ComboboxOptions,
	ComboboxOption,
	ComboboxButton,
} from "@headlessui/vue"
import { Popover } from "frappe-ui"
import CustomIcons from "@/components/desk/global/CustomIcons.vue"

export default {
	name: "Autocomplete",
	props: ["modelValue", "options", "placeholder", "width"],
	emits: ["update:modelValue", "change"],
	components: {
		Popover,
		CustomIcons,
		Combobox,
		ComboboxInput,
		ComboboxOptions,
		ComboboxOption,
		ComboboxButton,
	},
	data() {
		return {
			query: "",
		}
	},
	computed: {
		valuePropPassed() {
			return "value" in this.$attrs
		},
		selectedValue: {
			get() {
				return this.valuePropPassed
					? this.$attrs.value
					: this.modelValue
			},
			set(val) {
				this.query = ""
				this.$emit(
					this.valuePropPassed ? "change" : "update:modelValue",
					val
				)
			},
		},
		filteredOptions() {
			if (!this.query) {
				return this.options
			}
			return this.options.filter((option) => {
				let searchTexts = [option.label, option.value]
				return searchTexts.some((text) =>
					(text || "")
						.toLowerCase()
						.includes(this.query.toLowerCase())
				)
			})
		},
	},
	methods: {
		displayValue(option) {
			if (typeof option === "string") {
				return option
			}
			return option?.label
		},
		foo() {
			console.log("foo")
		},
	},
}
</script>
