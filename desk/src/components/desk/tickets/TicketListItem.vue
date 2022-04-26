––<template>
	<div class="block select-none rounded-[6px] py-[7px] px-[11px]" :class="selected ? 'bg-blue-50 hover:bg-blue-100' : 'hover:bg-gray-50'">
		<div 
			v-if="ticket"
			class="group flex items-center text-base"
		>
			<div 
				@mouseover="() => {toggleSelectBox = true}" 
				@mouseleave="() => {toggleSelectBox = false}"
				class="w-[37px] h-[14px] flex items-center"
			>
				<FeatherIcon 
					v-if="ticket.priority && ticket.priority == 'Urgent' && !toggleSelectBox && !selected"
					class="w-4 h-4 stroke-red-500 stroke-2" 
					name="arrow-up"
				/>
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
					:class="ticket.seen ? 'font-normal text-gray-600' : 'font-semibold text-gray-800'"
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
							<div class="stroke-green-600 stroke-red-600 stroke-yellow-600 w-0 h-0 block"></div>
							<div 
								v-if="ticket.status"
								@click="toggleStatuses"	
								class="flex items-center space-x-1"
							>
								<CustomIcons 
									:name="
										ticket.status == 'Open' ? 'comment' :
										['Closed', 'Resolved'].includes(ticket.status) ? 'lock' : 'comment'
									"
									class="w-[16px] h-[16px]" :class="`${['Closed', 'Resolved'].includes(ticket.status) ? 'fill-gray-600' : ''} stroke-${getBadgeColorBasedOnStatus(ticket.status)}-600`" 
								/>
								<div class="cursor-pointer text-base font-normal" :class="`text-${getBadgeColorBasedOnStatus(ticket.status)}-600`">{{ ticket.status }}</div>
							</div>
						</div>
					</template>
				</Dropdown>
			</div>
			<div class="sm:w-3/12">
				<div class="truncate w-40 text-gray-600 font-normal" v-if="ticket.contact">{{ ticket.contact.name }}</div>
			</div>
			<div class="sm:w-2/12 font-normal">
				<div 
					v-if="getResolutionDueIn()" 
					:class="getResolutionBadgeColor()"
				>
					{{ getResolutionDueIn() }}
				</div>
			</div>
			<div class="sm:w-1/12 text-gray-600 font-normal">
				{{ $dayjs.shortFormating($dayjs(ticket.modified).fromNow()) }}
			</div>
			<div class="pt-[-3px] w-[50.37px]">
				<div>
					<Dropdown
						v-if="agents"
						placement="right" 
						:options="agentsAsDropdownOptions()" 
						:dropdown-width-full="true"
						class="text-base flex flex-row-reverse"
					>
						<template v-slot="{ toggleAssignees }">
							<div @click="toggleAssignees" class="cursor-pointer">
								<div v-if="ticket.assignees.length > 0">
									<div v-for="assignee in ticket.assignees" :key="assignee">
										<Avatar class="h-[26px] w-[26px]" :label="assignee.agent_name" :imageURL="assignee.image" />
									</div>
								</div>
								<div v-else class="invisible group-hover:visible">
									<Avatar class="bg-blue-50 h-[26px] w-[26px]" />
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

export default {
	name: 'TicketListItem',
	props: ['ticketId', 'selected'],
	components: {
		Input,
		Badge,
		Dropdown,
		FeatherIcon,
		Avatar,
		CustomIcons
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
		getBadgeColorBasedOnStatus(status) {
			if (['Open'].includes(status)) {
				return 'green'
			}
			if (['Closed', 'Resolved'].includes(status)) {
				return 'gray'
			}
			if (['Replied'].includes(status)) {
				return 'yellow'
			}
			if (['On Hold'].includes(status)) {
				return 'blue'
			}
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
		getIconBasedOnPriority(priority) {
			if (priority == 'High') {
				return 'arrow-up'
			}
			if (priority == 'Medium') {
				return 'arrow-up'
			}
			if (priority == "Low") {
				return 'arrow-down'
			}
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