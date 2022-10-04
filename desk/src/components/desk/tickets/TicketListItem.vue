<template>
	<div
		class="block select-none rounded-[6px] py-[7px] pl-[11px] pr-[9px]"
		:class="selected ? 'bg-blue-50 hover:bg-blue-100' : 'hover:bg-gray-50'"
	>
		<div
			v-if="ticket"
			@pointerover="
				() => {
					toggleSelectBox = true
				}
			"
			@pointerleave="
				() => {
					toggleSelectBox = false
				}
			"
			class="group flex items-center text-base"
		>
			<div class="w-[37px] h-[14px] flex items-center">
				<CustomIcons
					v-if="!toggleSelectBox && !selected"
					:name="`priority-${ticket.priority.toLowerCase()}`"
					class="h-3 w-3"
					:style="ticket.status == 'Closed' ? 'opacity: 0.5;' : ''"
				/>
				<Input
					v-if="toggleSelectBox || selected"
					type="checkbox"
					@click="$emit('toggleSelect')"
					:checked="selected"
					class="cursor-pointer"
				/>
			</div>
			<div
				class="sm:w-1/12 text-gray-600 font-normal"
				:style="getOpacityStyleBasedOnStatus(ticket.status)"
			>
				{{ ticket.name }}
			</div>
			<div class="sm:w-7/12">
				<router-link
					:to="`/frappedesk/tickets/${ticket.name}`"
					class="flex items-center space-x-[8px]"
					:style="getOpacityStyleBasedOnStatus(ticket.status)"
				>
					<div
						class="truncate max-w-fit lg:w-80 md:w-52 sm:w-40"
						:class="
							!seen
								? 'font-semibold text-gray-800'
								: ['Closed', 'Resolved'].includes(ticket.status)
								? 'font-normal text-gray-600'
								: 'font-normal text-gray-900'
						"
					>
						{{ ticket.subject }}
					</div>
					<div
						v-if="ticket.ticket_type"
						class="text-gray-600 font-medium bg-gray-200 px-[8px] py-[2px] rounded-[48px] uppercase text-xs"
					>
						{{ ticket.ticket_type }}
					</div>
				</router-link>
			</div>
			<div
				class="sm:w-3/12"
				:style="getOpacityStyleBasedOnStatus(ticket.status)"
			>
				<div class="w-full">
					<div
						v-if="false"
						class="stroke-green-600 stroke-red-600 stroke-yellow-600 w-0 h-0"
					></div>
					<div
						v-if="ticket.status"
						@click="toggleStatuses"
						class="flex flex-row items-center space-x-1"
					>
						<FeatherIcon
							v-if="ticket.status != 'Open'"
							:name="
								{
									Closed: 'lock',
									Resolved: 'check',
									Replied: 'corner-up-left',
								}[ticket.status]
							"
							class="stroke-gray-600 w-[12px] h-[12px] mx-[2px]"
						/>
						<CustomIcons
							v-else
							name="comment"
							class="w-[16px] h-[16px] stroke-green-600"
						/>
						<div
							class="text-base font-normal"
							:class="getColorBasedOnStatus(ticket.status)"
						>
							{{ ticket.status }}
						</div>
					</div>
				</div>
			</div>
			<div
				class="sm:w-3/12"
				:style="getOpacityStyleBasedOnStatus(ticket.status)"
			>
				<div
					class="truncate w-40 text-gray-600 font-normal"
					v-if="ticket.contact"
				>
					{{ ticket.contact }}
				</div>
			</div>
			<div
				class="sm:w-2/12 font-normal"
				:style="getOpacityStyleBasedOnStatus(ticket.status)"
			>
				<a
					v-if="getResolutionDueIn()"
					:title="$dayjs(ticket.resolution_by)"
					:class="getResolutionBadgeColor()"
				>
					{{ getResolutionDueIn() }}
				</a>
			</div>
			<div class="sm:w-1/12">
				<a
					:title="$dayjs(ticket.modified)"
					class="text-gray-600 font-normal"
					:style="getOpacityStyleBasedOnStatus(ticket.status)"
				>
					{{
						$dayjs.shortFormating($dayjs(ticket.modified).fromNow())
					}}
				</a>
			</div>
			<div class="pt-[-3px] sm:w-1/12 ml-[2px]">
				<div>
					<div class="text-base flex flex-row-reverse">
						<div class="h-[26px] w-[26px]">
							<div v-if="assignees.length > 0">
								<div
									v-for="assignee in assignees"
									:key="assignee"
								>
									<Avatar
										class="h-[26px] w-[26px]"
										:imageURL="assignee.user_image"
										:label="assignee.agent_name"
									/>
								</div>
							</div>
						</div>
					</div>
				</div>
			</div>
		</div>
		<div class="transform translate-y-2" />
	</div>
</template>

<script>
import { Badge, Dropdown, Input, FeatherIcon, Avatar } from "frappe-ui"
import CustomIcons from "@/components/desk/global/CustomIcons.vue"
import { inject, ref } from "vue"

export default {
	name: "TicketListItem",
	props: ["ticket", "selected"],
	components: {
		Input,
		Badge,
		Dropdown,
		FeatherIcon,
		Avatar,
		CustomIcons,
	},
	setup() {
		const user = inject("user")
		const agents = inject("agents")
		const toggleSelectBox = ref(false)

		return {
			user,
			agents,
			toggleSelectBox,
		}
	},
	computed: {
		assignees() {
			if (this.ticket._assign) {
				const result = []
				JSON.parse(this.ticket._assign).forEach((assignee) => {
					const agent = this.agents.find((x) => x.name === assignee)
					if (agent) {
						result.push(agent)
					}
				})
				return result
			}
			return []
		},
		seen() {
			let seenFlag = false
			if (this.ticket._seen) {
				JSON.parse(this.ticket._seen).forEach((seen) => {
					if (seen === this.user.user) {
						seenFlag = true
					}
				})
			}
			return seenFlag
		},
	},
	methods: {
		getOpacityStyleBasedOnStatus(status) {
			return ["Closed", "Resolved"].includes(status)
				? "opacity: 0.8;"
				: ""
		},
		getColorBasedOnStatus(status) {
			return status == "Open" ? "text-green-600" : "text-gray-600"
		},
		getColorBasedOnPriority(priority, type) {
			let sufix = ""
			if (type == "icon") {
				sufix = "stroke"
			} else if (type == "text") {
				sufix = "text"
			}
			let color = ""
			if (priority == "High") {
				color = "red-500"
			} else if (priority == "Medium") {
				color = "yellow-500"
			} else if (priority == "Low") {
				color = "green-500"
			}

			return sufix ? sufix + "-" + color : color
		},
		getResolutionDueIn() {
			let resolutionBy = this.ticket.resolution_by
			let agreementStatus = this.ticket.agreement_status

			if (["Fulfilled", "Overdue"].includes(agreementStatus)) {
				return agreementStatus
			}
			let resolutionString = this.$dayjs.shortFormating(
				this.$dayjs().to(resolutionBy)
			)
			if (["Resolution Due"].includes(agreementStatus)) {
				return this.ticket.resolution_by ? resolutionString : ""
			}
			return resolutionString
		},
		getResolutionBadgeColor() {
			let resolutionDueIn = this.getResolutionDueIn()
			switch (resolutionDueIn) {
				case "Fulfilled":
					return "text-gray-600"
				case "Overdue":
					return "text-red-500"
				default:
					return "text-gray-600"
			}
		},
	},
}
</script>

<style></style>
