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
			value
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
	setup() {
		const manager = inject("manager")

		return {
			manager,
		}
	},
	computed: {
		status() {
			return this.filter.value ? "completed" : "editing"
		},
		operatorOptions() {
			// TODO fetch doctype fieldtype and return options accordingly
			// TODO: use a single api to fetch the operator options for a fieldname, parameters will be doctype & fieldname
			let operators = this.$resources.operators.data || []
			return operators.map((operator) => {
				return {
					label: operator,
				}
			})
		},
	},
	// watch: {
	// status() {
	// 	if (this.status === "completed") {
	// 		this.manager.addFilter(this.filter)
	// 	}
	// },
	// },
	mounted() {
		// TODO: check if this is too hacky? can be removed once Dropdown has a focus method
		let a = document.getElementById(
			`filter-item-operator-dropdown-${this.filter.fieldname}`
		)
		a.click()
	},
	resources: {
		operators() {
			return {
				method: "frappedesk.api.general.get_filter_operators_for_field",
				params: {
					doctype: this.manager.options.doctype,
					fieldname: this.filter.fieldname,
				},
				auto: true,
			}
		},
	},
}
</script>
