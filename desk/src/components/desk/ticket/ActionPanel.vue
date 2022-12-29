<template>
	<div v-if="ticket" class="flex flex-col h-full">
		<div class="pl-[19px] pr-[17px] pt-[18px] pb-[28px] dashes">
			<div class="text-base space-y-[11px]">
				<div class="flex flex-col space-y-[2px]">
					<div class="flex flex-row space-x-[5.33px] items-center">
						<div class="text-gray-600 text-[12px]">
							First Response Due
						</div>
						<CustomIcons
							v-if="firstResponseStatus()"
							:name="
								{ Success: 'sla-pass', Failed: 'sla-fail' }[
									firstResponseStatus()
								]
							"
							class="w-[16px] h-[16px]"
						/>
					</div>
					<div class="font-normal text-gray-900">
						{{
							getFormatedDate(
								ticket.response_by,
								"ddd, MMM DD, HH:mm"
							)
						}}
					</div>
				</div>
				<div class="flex flex-col space-y-[2px]">
					<div class="flex flex-row space-x-[5.33px] items-center">
						<div class="text-gray-600 text-[12px]">
							Resolution Due
						</div>
						<CustomIcons
							v-if="resolutionStatus() != 'Paused'"
							:name="
								{ Success: 'sla-pass', Failed: 'sla-fail' }[
									resolutionStatus()
								]
							"
							class="w-[16px] h-[16px]"
						/>
						<Badge v-else color="blue">Paused</Badge>
					</div>
					<div class="font-normal text-gray-900">
						{{
							getFormatedDate(
								ticket.resolution_by,
								"ddd, MMM DD, HH:mm"
							)
						}}
					</div>
				</div>
			</div>
		</div>
		<div>
			<span
				class="dot fixed ml-[-1px] mt-[-10.5px] bg-gray-50 border-r border-t border-b"
			></span>
			<span
				class="dot rotate-180 fixed ml-[241.5px] mt-[-10.5px] bg-white border-r border-t border-b"
			></span>
		</div>
		<div
			class="px-[19px] py-[28px] h-full overflow-y-auto flex flex-col space-y-2.5"
		>
			<div
				class="flex flex-col space-y-[12px] pb-5"
				:class="{ 'border-b': customFields?.length > 0 }"
			>
				<!-- Show system ticket fields: Status, Ticket Type, Priority and Agent Group  -->
				<div
					v-for="fieldname in [
						'_assign',
						'status',
						'ticket_type',
						'priority',
						'agent_group',
					]"
					:key="fieldname"
				>
					<TicketField
						:ref="`field-${fieldname}-input`"
						:ticketId="ticket.name"
						:fieldname="fieldname"
						:editable="true"
						:validate="
							function () {
								// remove the validation error, from current field if any (since the value is updated)
								if (validationErrorFields.includes(fieldname)) {
									validationErrorFields.splice(
										validationErrorFields.indexOf(
											fieldname
										),
										1
									)
								}
								if (fieldname === 'status') {
									if (!ticket.ticket_type) {
										validationErrorFields.push(
											'ticket_type'
										)
										return false
									}
								}
								return true
							}
						"
						:triggerValidationError="
							validationErrorFields.includes(fieldname)
						"
					/>
				</div>
			</div>
			<div class="flex flex-col space-y-[12px]">
				<!-- Show all the ticket custom fields that can be viewed by an agent -->
				<div
					v-for="customField in customFields"
					:key="customField.fieldname"
				>
					<TicketField
						:ticketId="ticket.name"
						:fieldname="customField.fieldname"
						:editable="customField.is_editable_by_agent"
					/>
				</div>
			</div>
		</div>
	</div>
</template>

<script>
import { FeatherIcon, Badge } from "frappe-ui"
import { inject, ref } from "@vue/runtime-core"
import TicketField from "@/components/global/TicketField.vue"
import CustomIcons from "@/components/desk/global/CustomIcons.vue"

export default {
	name: "ActionPanel",
	props: ["ticketId"],
	components: {
		Badge,
		FeatherIcon,
		TicketField,
		CustomIcons,
	},
	setup() {
		const user = inject("user")
		const validationErrorFields = ref([])
		return {
			user,
			validationErrorFields,
		}
	},
	mounted() {
		document.addEventListener("keydown", this.handleShortcuts.bind(this))
	},
	unmounted() {
		document.removeEventListener("keydown", this.handleShortcuts)
	},
	updated() {
		var elems = document.querySelectorAll(".error-animation")
		setTimeout(function () {
			;[].forEach.call(elems, function (el) {
				el.classList.remove("error-animation")
			})
		}, 820)
	},
	computed: {
		customFields() {
			return this.$resources.customFields.data || null
		},
		ticket() {
			return this.$resources.ticket.doc || null
		},
	},
	resources: {
		customFields() {
			return {
				method: "frappedesk.api.ticket.get_custom_fields",
				params: {
					doctype: "Ticket",
					view: "Agent Portal",
				},
				auto: true,
			}
		},
		ticket() {
			return {
				type: "document",
				doctype: "Ticket",
				name: this.ticketId,
			}
		},
	},
	methods: {
		handleShortcuts(e) {
			if ((e.metaKey || e.ctrlKey) && e.altKey) {
				e.preventDefault()
				switch (e.keyCode) {
					case 82:
						this.updateStatus("Replied")
						break
					case 69:
						this.updateStatus("Resolved")
						break
					case 67:
						this.updateStatus("Closed")
				}
			}
		},
		getFormatedDate(date, format) {
			return date ? this.$dayjs(date).format(format) : ""
		},
		firstResponseStatus() {
			if (this.ticket.first_responded_on) {
				return this.ticket.response_by > this.ticket.first_responded_on
					? "Success"
					: "Failed"
			} else {
				return null
			}
		},
		resolutionStatus() {
			switch (this.ticket.agreement_status) {
				case "Resolution Due":
					return this.ticket.resolution_by ? "" : "Paused"
				case "Fulfilled":
					return "Success"
				case "Overdue":
					return "Failed"
				default:
					return ""
			}
		},
	},
}
</script>

<style>
.dashes {
	background-image: linear-gradient(
		to right,
		#ebeef0 33%,
		rgba(255, 255, 255, 0) 0%
	);
	background-position: bottom;
	background-size: 19.5px 1px;
	background-repeat: repeat-x;
}
.dot {
	height: 21px;
	width: 10.5px;
	border-radius: 0 10.5px 10.5px 0;
	display: inline-block;
}
.error-animation {
	animation: shake 0.82s cubic-bezier(0.36, 0.07, 0.19, 0.97) both;
	transform: translate3d(0, 0, 0);
	backface-visibility: hidden;
	perspective: 1000px;
}

@keyframes shake {
	10%,
	90% {
		transform: translate3d(-1px, 0, 0);
	}

	20%,
	80% {
		transform: translate3d(2px, 0, 0);
	}

	30%,
	50%,
	70% {
		transform: translate3d(-4px, 0, 0);
	}

	40%,
	60% {
		transform: translate3d(4px, 0, 0);
	}
}
</style>
