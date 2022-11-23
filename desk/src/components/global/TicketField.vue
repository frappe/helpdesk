<template>
	<div
		v-if="!$resources.fieldMetaInfo.loading"
		class="flex flex-col space-y-[8px]"
	>
		<div class="text-[12px] text-gray-600">
			{{ fieldMetaInfo.label }}
		</div>
		<div>
			<!-- Data field -->
			<Input
				v-if="fieldMetaInfo.fieldtype === 'Data'"
				type="text"
				@change="debouncedOnInput"
				:value="fieldValue"
			/>
			<!-- Link / Select field -->
			<Autocomplete
				v-else
				:placeholder="`Select ${fieldMetaInfo.label.toLowerCase()}`"
				:value="fieldValue"
				@change="onInput"
				:resourceOptions="getResourceOptions()"
			/>
		</div>
	</div>
</template>

<script>
import Autocomplete from "@/components/global/Autocomplete.vue"
import { debounce } from "frappe-ui"

export default {
	name: "TicketField",
	props: {
		ticketId: {
			type: Number,
			required: true,
		},
		fieldname: {
			type: String,
			required: true,
		},
		// TODO: use a prop to trigger mandatory field validation errors: use case (ticket type should be set before changing ticket status)
	},
	components: {
		Autocomplete,
	},
	emits: ["validate", "update"], // validate can be used to triger external validations, eg: before updating ticket status, ticket type should be set, etc
	inject: ["ticketController"], // TODO: use ticket controller to fetch field values and update ticket, instead of individual apis
	computed: {
		fieldMetaInfo() {
			return this.$resources.fieldMetaInfo.data || {}
		},
		fieldValue() {
			return this.$resources.fieldValue.data || ""
		},
	},
	resources: {
		fieldMetaInfo() {
			// field can be a custom or a standard field
			// field type : Data, Link, Select
			// field label
			// field permissions: read, write (based on is agent / customer)
			return {
				method: "frappedesk.api.ticket.get_field_meta_info",
				params: {
					fieldname: this.fieldname,
				},
				auto: true,
			}
		},
		fieldValue() {
			// field can be a custom or a standard field
			return {
				method: "frappedesk.api.ticket.get_field_value",
				params: {
					ticket_id: this.ticketId,
					fieldname: this.fieldname,
				},
				auto: true,
			}
		},
		updateFieldValue() {
			return {
				method: "frappedesk.api.ticket.update_field_value",
				params: {
					ticket_id: this.ticketId,
					fieldname: this.fieldname,
					value: this.value,
				},
			}
		},
	},
	methods: {
		onInput(val) {
			console.log(
				this.fieldMetaInfo.fieldtype,
				" input for ",
				this.fieldMetaInfo.label,
				" value: ",
				val.target.value
			)
		},
		debouncedOnInput: debounce(function (val) {
			// for datepicker & text input, inputs only
			// intermediate parameter is used to restric updating url query filters on every input
			console.log("text input value value", val.target.value)
		}, 300),
		getResourceOptions() {
			console.log(
				this.fieldMetaInfo.fieldname,
				this.fieldMetaInfo.fieldtype
			)
			switch (this.fieldMetaInfo.fieldtype) {
				case "Link":
					return {
						method: "frappe.client.get_list",
						inputMap: (query) => {
							return {
								doctype: this.fieldMetaInfo.options,
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
						method: "frappedesk.api.general.get_filtered_select_field_options",
						inputMap: (query) => {
							return {
								doctype: "Ticket",
								fieldname: this.fieldMetaInfo.fieldname,
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
