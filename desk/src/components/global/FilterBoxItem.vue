<template>
	<div
		class="flex flex-row rounded bg-white shadow pl-1.5 pr-0.5 select-none"
	>
		<div class="py-0.5 px-1 text-gray-700">{{ filter.label }}</div>
		<Dropdown :options="operatorOptions">
			<template v-slot="{ toggle }">
				<div
					:id="`filter-item-operator-dropdown-${filter.fieldname}`"
					@click="toggle"
					role="button"
					class="hover:bg-gray-100 border-x py-0.5 px-1 text-gray-500"
				>
					{{ filter.filter_type || "operator" }}
				</div>
			</template>
		</Dropdown>
		<div
			v-if="filter.filter_type"
			role="button"
			class="hover:bg-gray-100 py-0.5"
		>
			<div v-if="['like', 'not like'].includes(filter.filter_type)">
				<input
					type="text"
					@input="(val) => onInput(val, true)"
					@change="(val) => onInput(val, false)"
					:value="filter.value"
					class="h-2 focus:ring-0 border-0 bg-transparent px-2 text-base text-gray-700"
				/>
			</div>
			<div v-else-if="['Link', 'Select'].includes(filter.data_type)">
				<Autocomplete
					class="px-1"
					:placeholder="`Select ${filter.label.toLowerCase()}`"
					:value="filter.value"
					@change="
						(item) => {
							if (!item) {
								return
							}
							// onInput is not used, since Autocomplete input already uses debounce for input handle
							filter.value = item.value
							$emit('add-filter')
						}
					"
					:resourceOptions="getResourceOptions(filter)"
					:searchable="true"
				>
					<template #input-holder="{ selectedValue }">
						<div class="text-gray-700">
							{{ selectedValue || "select a value" }}
						</div>
					</template>
				</Autocomplete>
			</div>
			<div v-else-if="['Datetime', 'Date'].includes(filter.data_type)">
				<input
					type="date"
					class="h-2 border-0 bg-transparent text-base text-gray-700 focus:ring-0 px-1"
					role="button"
					:value="filter.value"
					@input="(val) => onInput(val, false)"
				/>
			</div>
		</div>
		<div class="hover:bg-gray-100 p-1 rounded my-0.5" role="button">
			<FeatherIcon
				@click="$emit('remove-filter')"
				name="x"
				class="h-3 w-3"
			/>
		</div>
	</div>
</template>

<script>
import { FeatherIcon, Dropdown, debounce } from "frappe-ui"
import Autocomplete from "@/components/global/Autocomplete.vue"

export default {
	name: "FilterBoxItem",
	props: {
		filter: {
			type: Object,
			required: true,
		},
	},
	components: {
		FeatherIcon,
		Dropdown,
		Autocomplete,
	},
	inject: ["manager"],
	computed: {
		operatorOptions() {
			let getOperatorsForDataType = (dataType) => {
				switch (dataType) {
					case "Data":
						return ["like", "not like"]
					case "Link":
						return ["is", "is not", "like", "not like"]
					case "Datetime":
						return ["before", "after"] //, "between"]
					case "Date":
						return ["before", "after"] //, "between"]
					case "Select":
						return ["is", "is not"]
					default:
						return ["is", "is not"]
				}
			}
			let [dataType, options] = this.$resources.dataType.data || "Data"
			this.filter.data_type = dataType
			if (this.filter.data_type == "Link") {
				this.filter.link_doctype = options
			}
			return getOperatorsForDataType(dataType).map((operator) => {
				return {
					label: operator,
					onClick: () => {
						this.filter.filter_type = operator
						if (!this.filter.value) {
							this.toggleDropdown("value")
						} else {
							this.$emit("add-filter")
						}
					},
				}
			})
		},
	},
	mounted() {
		if (!this.filter.filter_type) {
			this.toggleDropdown("operator")
		}
	},
	resources: {
		dataType() {
			return {
				url: "helpdesk.api.general.get_field_data_type",
				params: {
					doctype: this.manager.options.doctype,
					fieldname: this.filter.fieldname,
				},
				auto: true,
			}
		},
		selectOptionsForField() {
			return {
				url: "helpdesk.api.general.get_select_options_for_field",
			}
		},
	},
	methods: {
		onInput: debounce(function (val, intermediate = true) {
			// for datepicker & text input, inputs only
			// intermediate parameter is used to restric updating url query filters on every input
			this.filter.value = val.target.value
			this.$emit("add-filter", intermediate)
		}, 300),
		toggleDropdown(item) {
			switch (item) {
				case "operator":
					let a = document.getElementById(
						`filter-item-${item}-dropdown-${this.filter.fieldname}`
					)
					a.click()
					break
				case "value":
					// TODO: open the dropdown / combobox / text input / date picker
					break
				default:
					break
			}
		},
		getResourceOptions(filter) {
			switch (filter.data_type) {
				case "Link":
					return {
						url: "helpdesk.extends.client.get_list",
						inputMap: (query) => {
							return {
								doctype: filter.link_doctype,
								pluck: "name",
								filters: [["name", "like", `%${query}%`]],
							}
						},
						responseMap: (res) => {
							return res.map((d) => {
								return {
									label: d.name,
									value: d.name,
								}
							})
						},
					}
				case "Select":
					return {
						url: "helpdesk.api.general.get_filtered_select_field_options",
						inputMap: (query) => {
							return {
								doctype: this.manager.options.doctype,
								fieldname: filter.fieldname,
								query,
							}
						},
						responseMap: (res) => {
							return res.map((d) => {
								return {
									label: d,
									value: d,
								}
							})
						},
					}
				default:
					return null
			}
		},
	},
}
</script>

<style scoped>
input[type="date"]::-webkit-calendar-picker-indicator {
	margin-left: -18px;
}
</style>
