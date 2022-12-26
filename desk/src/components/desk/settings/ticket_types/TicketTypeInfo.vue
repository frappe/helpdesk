<template>
	<div class="min-w-[490px] px-[24px] py-[10px]">
		<div class="shrink-0 h-[72px] py-[22px] flow-root px-[16px]">
			<div class="float-left">
				<router-link
					:to="`/frappedesk/settings/ticket_types`"
					class="my-1 text-[12px] text-gray-600 stroke-gray-600 flex flex-row items-center space-x-1 hover:text-gray-700 hover:stroke-gray-700 select-none"
					role="button"
				>
					<FeatherIcon name="arrow-left" class="w-[13px] h-[13px]" />
					<div>Back to ticket type list</div>
				</router-link>
			</div>
			<div class="float-right">
				<div class="flex flex-row space-x-2">
					<Button
						appearance="secondary"
						@click="
							() => {
								this.$router.go()
							}
						"
					>
						Cancel
					</Button>
					<Button appearance="primary" @click="saveDocument()">
						Save
					</Button>
				</div>
			</div>
		</div>
		<div
			class="flex flex-row space-x-[24px] h-full border-t px-[16px] py-[22px]"
		>
			<TicketTypeNameAndDescription
				class="grow"
				:name="values?.ticketTypeName"
				:description="values?.description"
				:priority="values?.priority"
				:editable="editMode"
				:ticketTypeResource="$resources.ticketType"
			/>
		</div>
	</div>
</template>
<script>
import { ref, provide } from "vue"
import { FeatherIcon, Input } from "frappe-ui"
import TicketTypeNameAndDescription from "@/components/desk/settings/ticket_types/TicketTypeNameAndDescription.vue"

export default {
	name: "TicketTypeInfo",
	props: ["ticketTypeId"],
	components: {
		FeatherIcon,
		Input,
		TicketTypeNameAndDescription,
	},
	setup(props) {
		const editingName = ref(false)
		const newTicketTypeTempValues = ref({})
		const updateNewTicketTypeInput = ref((input) => {
			newTicketTypeTempValues.value[input.field] = input.value
		})
		provide("updateNewTicketTypeInput", updateNewTicketTypeInput)
		provide("newTicketTypeTempValues", newTicketTypeTempValues)
		const saveTicketTypeNameAndDescription = ref(() => {})
		provide(
			"saveTicketTypeNameAndDescription",
			saveTicketTypeNameAndDescription
		)
		const tempTicketTypeName = ref("")
		const updatingValues = ref(false)
		const editMode = ref(!props.ticketTypeId)
		provide("editMode", editMode)

		return {
			editingName,
			tempTicketTypeName,
			updatingValues,
			editMode,
			newTicketTypeTempValues,
			saveTicketTypeNameAndDescription,
		}
	},
	computed: {
		ticketTypeDoc() {
			console.log(this.$resources.ticketType.doc, "docc")
			return this.$resources.ticketType.doc || null
		},
		values() {
			if (this.updatingValues) {
				return this.values || null
			}
			return {
				ticketTypeName: this.ticketTypeDoc?.name || null,
				description: this.ticketTypeDoc?.description || null,
				priority: this.ticketTypeDoc?.priority || null,
			}
		},
	},
	deactivated() {
		this.resetForm()
	},
	resources: {
		ticketType() {
			return {
				type: "document",
				doctype: "Ticket Type",
				name: this.ticketTypeId,
				setValue: {
					onSuccess: () => {
						this.$toast({
							title: "Ticket Type Updated.",
							customIcon: "circle-check",
							appearance: "success",
						})
					},
					onError: (err) => {
						this.$toast({
							title: "Error while updating ticket type",
							text: err,
							customIcon: "circle-fail",
							appearance: "danger",
						})
					},
				},
			}
		},
	},
	methods: {
		resetForm() {
			this.editingName = false
			this.tempTicketTypeName = this.values.ticketTypeName
		},
		save() {
			this.updatingValues = true
			const newValues = this.values
			this.$resources.user.setValue
				.submit({
					name: newValues.name,
					description: newValues.description,
				})
				.then(() => {
					this.$resources.ticketType.setValue.submit({
						name: this.tempTicketTypeName,
					})
				})
		},
		saveDocument() {
			const inputParams = {
				name: this.newTicketTypeTempValues.name,
				description: this.newTicketTypeTempValues.description,
				priority: this.newTicketTypeTempValues.priority,
			}
			this.$resources.ticketType.setValue.submit({
				...inputParams,
			})
			this.editMode = false
		},
		cancel() {
			this.$router.go()
		},
	},
}
</script>
