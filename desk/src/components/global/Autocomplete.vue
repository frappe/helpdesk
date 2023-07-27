<template>
	<Combobox
		v-model="selectedValue"
		nullable
		v-slot="{ open: isComboboxOpen }"
	>
		<Popover class="w-full">
			<template #target="{ open: openPopover }">
				<div class="w-full">
					<ComboboxButton
						class="w-full"
						@click="
							() => {
								if (searchable) {
									openPopover()
								}
							}
						"
					>
						<slot
							name="input-holder"
							:selectedValue="selectedValue"
						>
							<div
								class="h-[28px] flex items-center justify-between w-full py-1.5 pl-3 pr-2 rounded-md bg-gray-100"
								:class="{
									'rounded-b-none': isComboboxOpen,
								}"
							>
								<slot
									name="input"
									:selectedValue="selectedValue"
									:placeholder="searchable ? placeholder : ''"
								>
									<span
										class="text-base line-clamp-1"
										v-if="selectedValue"
									>
										{{ displayValue(selectedValue) }}
									</span>
									<span
										class="text-base text-gray-500"
										v-else
									>
										{{
											searchable ? placeholder : "" || ""
										}}
									</span>
								</slot>
								<CustomIcons
									v-if="searchable"
									name="select"
									class="w-[12px] h-[12px] stroke-gray-500"
								/>
							</div>
						</slot>
					</ComboboxButton>
				</div>
			</template>
			<template #body>
				<ComboboxOptions
					class="max-w-[240px] px-1.5 pb-1.5 bg-white rounded-md mt-2 border shadow-md max-h-[11rem] overflow-y-auto"
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
									if (resourceOptions) {
										dsearch(query)
									}
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
							class="px-2.5 py-1.5 cursor-pointer rounded-md text-base"
							:class="[{ 'bg-gray-100': active }]"
						>
							<Tooltip
								v-if="option.label.length > (20 * width) / 220"
								placement="top"
								:text="option.label"
							>
								<div
									:class="[
										'line-clamp-1',
										`w-[${width - 25 + 'px'}]`,
									]"
								>
									{{ option.label }}
								</div>
							</Tooltip>
							<div v-else>{{ option.label }}</div>
						</li>
					</ComboboxOption>
					<slot
						v-if="filteredOptions?.length == 0"
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
import { Popover, debounce } from "frappe-ui"
import CustomIcons from "@/components/desk/global/CustomIcons.vue"

export default {
	name: "Autocomplete",
	props: {
		modelValue: {
			type: Object,
			default: null,
		},
		options: {
			type: Array,
			default: () => [],
		},
		resourceOptions: {
			type: Function,
			default: () => {},
		},
		placeholder: {
			type: String,
		},
		searchable: {
			type: Boolean,
			default: true,
		},
		width: {
			type: Number,
			default: 250,
		},
		show: {
			type: Boolean,
			default: false,
		},
	},
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
	mounted() {
		this.dsearch("")
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
			if (!this.resourceOptions) {
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
			} else {
				let data = this.$resources.search.data || []
				if (data.length == 0) {
					return []
				}
				return this.resourceOptions.responseMap(data)
			}
		},
	},
	methods: {
		displayValue(option) {
			if (typeof option === "string") {
				return option
			}
			return option?.label
		},
		dsearch: debounce(function (query) {
			this.search(query)
		}, 300),
		search(query) {
			if (!this.searchable) return
			this.$resources.search.fetch(this.resourceOptions.inputMap(query))
		},
	},
	watch: {
		resourceOptions(val) {
			if (val) {
				this.$nextTick(() => {
					this.search("")
				})
			}
		},
	},
	resources: {
		search() {
			if (!this.resourceOptions) {
				return
			}
			return {
				url: this.resourceOptions.url,
			}
		},
	},
}
</script>
