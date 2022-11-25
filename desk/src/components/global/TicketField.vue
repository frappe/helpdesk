<template>
	<div class="flex flex-col space-y-[8px]">
		<div class="text-[12px] text-gray-600">
			{{ fieldMetaInfo?.label }}
		</div>
		<div>
			<!-- Data field -->
			<Input
				v-if="fieldMetaInfo?.fieldtype === 'Data'"
				type="text"
				@change="
					(val) => {
						onInput(val)
					}
				"
				:value="fieldValue"
				:debounce="300"
			/>
			<!-- Link / Select field -->
			<Autocomplete
				v-else
				:placeholder="`Select ${fieldMetaInfo?.label.toLowerCase()}`"
				:value="fieldValue"
				@change="
					(val) => {
						onInput(val)
					}
				"
				:resourceOptions="getResourceOptions()"
				:searchable="editable"
			/>
		</div>
	</div>
</template>

<script>
import Autocomplete from "@/components/global/Autocomplete.vue"
import { inject, computed } from "vue"

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
		editable: {
			type: Boolean,
			default: true,
		},
		// TODO: use a prop to trigger mandatory field validation errors: use case (ticket type should be set before changing ticket status)
	},
	components: {
		Autocomplete,
	},
	emits: ["validate"], // validate can be used to triger external validations, eg: before updating ticket status, ticket type should be set, etc
	setup(props, { context }) {
		const $tickets = inject("$tickets")
		const fieldValue = computed(() => {
			return $tickets.get(
				{ ticketId: props.ticketId, fieldname: props.fieldname },
				context
			).value
		})

		return {
			fieldValue,
		}
	},
	computed: {
		fieldMetaInfo() {
			return this.$resources.fieldMetaInfo.data || null
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
	},
	methods: {
		onInput(val) {
			if (!val) return
			let value = val.value
			this.$tickets.set(this.ticketId, this.fieldname, value).then(() => {
				this.$toast({
					title: "Ticket updated successfully.",
					appearance: "success",
					customIcon: "circle-check",
				})
			})
		},
		getResourceOptions() {
			if (!(this.editable || this.fieldMetaInfo)) return
			switch (this.fieldMetaInfo?.fieldtype) {
				case "Link":
					return {
						method: "frappe.client.get_list",
						inputMap: (query) => {
							return {
								doctype: this.fieldMetaInfo?.options,
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
								fieldname: this.fieldMetaInfo?.fieldname,
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
