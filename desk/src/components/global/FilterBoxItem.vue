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
			class="hover:bg-gray-100 py-0.5 px-1"
		>
			<div v-if="['like', 'not like'].includes(filter.filter_type)">
				text input
			</div>
			<div v-else-if="['Link', 'Select'].includes(filter.data_type)">
				{{
					`combobox / dropdown via ${
						filter.data_type == "Link" ? "get_list" : "api"
					}`
				}}
			</div>
			<div v-else-if="['Datetime', 'Date'].includes(filter.data_type)">
				date picker
			</div>
		</div>
		<div class="hover:bg-gray-100 p-1 rounded my-0.5" role="button">
			<FeatherIcon name="x" class="h-3 w-3" />
		</div>
	</div>
</template>

<script>
import { FeatherIcon, Dropdown } from "frappe-ui"
import { inject } from "vue"

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
	},
	inject: ["manager"],
	computed: {
		status() {
			return this.filter.value ? "completed" : "editing"
		},
		operatorOptions() {
			let getOperatorsForDataType = (dataType) => {
				switch (dataType) {
					case "Data":
						return ["like", "not like"]
					case "Link":
						return ["is", "is not", "like", "not like"]
					case "Datetime":
						return ["at", "before", "after"] //, "between"]
					case "Date":
						return ["at", "before", "after"] //, "between"]
					case "Select":
						return ["is", "is not"]
					default:
						return ["is", "is not"]
				}
			}
			let dataType = this.$resources.dataType.data || "Data"
			this.filter.data_type = dataType
			return getOperatorsForDataType(dataType).map((operator) => {
				return {
					label: operator,
					handler: () => {
						this.filter.filter_type = operator
						this.toggleDropdown("value")
					},
				}
			})
		},
	},
	watch: {
		status() {
			if (this.status === "completed") {
				this.manager.addFilter(this.filter)
			}
		},
	},
	mounted() {
		// TODO: check if this is too hacky? can be removed once Dropdown has a focus method
		this.toggleDropdown("operator")
	},
	resources: {
		dataType() {
			return {
				method: "frappedesk.api.general.get_field_data_type",
				params: {
					doctype: this.manager.options.doctype,
					fieldname: this.filter.fieldname,
				},
				auto: true,
			}
		},
		getList() {
			return {
				method: "frappe.client.get_list",
			}
		},
		selectOptionsForField() {
			return {
				method: "frappedesk.api.general.get_select_options_for_field",
			}
		},
	},
	methods: {
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
	},
}
</script>
