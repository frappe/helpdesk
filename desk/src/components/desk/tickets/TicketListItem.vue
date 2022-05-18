––<template>
	<div class="block select-none rounded-[6px] py-[7px] px-[11px]" :class="selected ? 'bg-blue-50 hover:bg-blue-100' : 'hover:bg-gray-50'">
		<div 
			v-if="ticket"
			class="group flex items-center text-base"
			:style="ticket.status == 'Closed' ? 'opacity: 0.5;': ''"
		>
			<div 
				@mouseover="() => {toggleSelectBox = true}" 
				@mouseleave="() => {toggleSelectBox = false}"
				class="w-[37px] h-[14px] flex items-center"
			>
				<CustomIcons v-if="!toggleSelectBox && !selected" :name="`priority-${ticket.priority.toLowerCase()}`" class="h-3 w-3" />
				<Input
					v-if="toggleSelectBox || selected"
					type="checkbox" 
					@click="$emit('toggleSelect')" 
					:checked="selected" 
					class="cursor-pointer mr-2" 
				/>
			</div>
			<div class="sm:w-1/12 text-gray-600 font-normal">
				{{ ticket.name }}
			</div>
			<router-link 
				:to="`/frappedesk/tickets/${ticket.name}`"
				class="sm:w-8/12 flex items-center space-x-[8px]"
			>
				<div 
					class="truncate max-w-fit lg:w-80 md:w-52 sm:w-40" 
					:class="!ticket.seen ? 'font-semibold text-gray-800' : (ticket.status == 'Closed' ? 'font-normal text-gray-600' : 'font-normal text-gray-900')"
				>
					{{ ticket.subject }}
				</div>
				<div v-if="ticket.ticket_type" class="text-gray-600 font-medium bg-gray-200 px-[8px] py-[2px] rounded-[48px] uppercase text-xs">{{ ticket.ticket_type }}</div>
			</router-link>
			<div class="sm:w-2/12">
				<Dropdown
					v-if="ticketStatuses"
					placement="left" 
					:options="statusesAsDropdownOptions()" 
					:dropdown-width-full="true"
				>
					<template v-slot="{ toggleStatuses }">
						<div class="w-full">
							<div v-if="false" class="stroke-green-600 stroke-red-600 stroke-yellow-600 w-0 h-0"></div>
							<div 
								v-if="ticket.status"
								@click="toggleStatuses"	
								class="flex flex-row items-center space-x-1"
							>
								<FeatherIcon v-if="ticket.status != 'Open'" :name="{ Closed: 'lock', Resolved: 'check', Replied: 'corner-up-left' }[ticket.status]" class="stroke-gray-600 w-[12px] h-[12px] mx-[2px]" />
								<CustomIcons v-else name="comment" class="w-[16px] h-[16px] stroke-green-600" />
								<div class="cursor-pointer text-base font-normal" :class="`text-${getColorBasedOnStatus(ticket.status)}-600`">{{ ticket.status }}</div>
							</div>
						</div>
					</template>
				</Dropdown>
			</div>
			<div class="sm:w-3/12">
				<div class="truncate w-40 text-gray-600 font-normal" v-if="ticket.contact">{{ ticket.contact.name }}</div>
			</div>
			<div class="sm:w-2/12 font-normal">
				<a 
					v-if="getResolutionDueIn()" 
					:title="$dayjs(ticket.resolution_by)"
					:class="getResolutionBadgeColor()"
				>
					{{ getResolutionDueIn() }}
				</a>
			</div>
			<a :title="$dayjs(ticket.modified)" class="sm:w-1/12 text-gray-600 font-normal">
				{{ $dayjs.shortFormating($dayjs(ticket.modified).fromNow()) }}
			</a>
			<div class="pt-[-3px] w-[50.37px]">
				<div>
					<Dropdown
						v-if="agents"
						placement="right" 
						:options="agentsAsDropdownOptions()" 
						:dropdown-width-full="true"
					>
						<template v-slot="{ toggleAssignees }">
							<div class="text-base flex flex-row-reverse">
								<div @click="toggleAssignees" class="cursor-pointer">
									<div v-if="ticket.assignees.length > 0">
										<div v-for="assignee in ticket.assignees" :key="assignee">
											<Avatar class="h-[26px] w-[26px]" :label="assignee.agent_name" :imageURL="assignee.image" />
										</div>
									</div>
									<div v-else class="invisible group-hover:visible">
										<div class="h-[26px] w-[26px] bg-blue-50 rounded-[26px] p-[6px]">
											<CustomIcons name="user-plus" />
										</div>
									</div>
								</div>
							</div>
						</template>
					</Dropdown>
				</div>
			</div>
		</div>
		<div class="transform translate-y-2"/>
	</div>
</template>

<script>
import { Badge, Dropdown, Input, FeatherIcon, Avatar } from 'frappe-ui'
import CustomIcons from '@/components/desk/global/CustomIcons.vue'
import { inject, ref } from 'vue'
import CustomIcons1 from '../global/CustomIcons.vue'

export default {
	name: 'TicketListItem',
	props: ['ticketId', 'selected'],
	components: {
    Input,
    Badge,
    Dropdown,
    FeatherIcon,
    Avatar,
    CustomIcons,
    CustomIcons1
},
	setup() {
		// values
		const user = inject('user')

		const tickets = inject('tickets')
		const ticketTypes = inject('ticketTypes')
		const ticketPriorities = inject('ticketPriorities')
		const ticketStatuses = inject('ticketStatuses')

		const agents = inject('agents')

		// controllers
		const ticketController = inject('ticketController')

		const toggleSelectBox = ref(false)

		return {
			user,
			
			tickets,
			ticketTypes,
			ticketPriorities,
			ticketStatuses,

			agents,

			ticketController,
			toggleSelectBox
		 }
	},
	computed: {
		ticket() {
			return this.tickets[this.ticketId] || null
		}
	},
	methods: {
		getColorBasedOnStatus(status) {
			return (status == 'Open') ? 'green' : 'gray'
		},
		getColorBasedOnPriority(priority, type) {
			let sufix = '';
			if (type == 'icon') { 
				sufix = 'stroke';
			} else if (type == 'text') {
				sufix = 'text';
			}
			let color = '';
			if (priority == 'High') {
				color = 'red-500'
			} else if (priority == 'Medium') {
				color = 'yellow-500'
			} else if (priority == "Low") {
				color = 'green-500'
			}

			return sufix ? sufix + '-' + color : color;
		},
		agentsAsDropdownOptions() {
			let agentItems = [];
			if (this.agents) {
				this.agents.forEach(agent => {
					agentItems.push({
						label: agent.agent_name,
						handler: () => {
							this.ticketController.set(this.ticketId, 'agent', agent.name)
						},
					});
				});
				let options = [];
				if (this.user.agent) {
					options.push({
						group: 'Myself',
						hideLabel: true,
						items: [
							{
								label: 'Assign to me',
								handler: () => {
									this.ticketController.set(this.ticketId, 'agent')
								}
							},
						],
					})
				}
				options.push({
					group: 'All Agents',
					hideLabel: true,
					items: agentItems,
				})
				return options;
			} else {
				return null;
			}
		},
		typesAsDropdownOptions() {
			let typeItems = [];
			if (this.ticketTypes) {
				this.ticketTypes.forEach(type => {
					typeItems.push({
						label: type.name,
						handler: () => {
							this.ticketController.set(this.ticketId, 'type', type.name)
						},
					});
				});
				return typeItems;
			} else {
				return null;
			}
		},
		statusesAsDropdownOptions() {
			let statusItems = [];
			if (this.ticketStatuses) {
				this.ticketStatuses.forEach(status => {
					statusItems.push({
						label: status,
						handler: () => {
							this.ticketController.set(this.ticketId, 'status', status)
						},
					});
				});
				return statusItems;
			} else {
				return null;
			}
		},
		prioritiesAsDropdownOptions() {
			let priorityItems = [];
			if (this.ticketPriorities) {
				this.ticketPriorities.forEach(priority => {
					priorityItems.push({
						label: priority.name,
						handler: () => {
							this.ticketController.set(this.ticketId, 'priority', priority.name)
						},
					});
				});
				return priorityItems;
			} else {
				return null;
			}
		},
		getResolutionDueIn() {
			let resolutionBy = this.ticket.resolution_by
			let agreementStatus = this.ticket.agreement_status

			if (["Fulfilled", "Overdue"].includes(agreementStatus)) {
				return agreementStatus;
			}
			let resolutionString = this.$dayjs.shortFormating(this.$dayjs().to(resolutionBy));
			if (["Resolution Due"].includes(agreementStatus)) {
				return this.ticket.resolution_by ? resolutionString : ''
			}
			return resolutionString;
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
		}
	}
}
</script>

<style>

</style>