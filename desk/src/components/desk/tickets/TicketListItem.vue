––<template>
	<div class="block hover:bg-gray-50 border-b">
		<div 
			v-if="ticket"
			class="group flex items-center text-base h-10"
		>
			<router-link 
				:to="`/helpdesk/tickets/${ticket.name}`"
				class="mr-4 sm:w-6/12 flex items-center space-x-2"
			>
				<Input type="checkbox" value="" />
				<div class="flex items-center grow space-x-1">
					<div class="font-medium truncate max-w-fit lg:w-96 md:w-64 sm:w-40">{{ ticket.subject }}</div>
					<div class="hidden md:block ml-1 text-base text-slate-400">#{{ ticket.name }}</div>
					<div>
						<FeatherIcon 
							v-if="ticket.priority"
							class="w-3 h-3" 
							:name="getIconBasedOnPriority(ticket.priority)"
						/>
					</div>
				</div>
			</router-link>
			<div class="hidden md:block lg:w-2/12">
				<div class="truncate w-40" v-if="ticket.contact">{{ ticket.contact.name }}</div>
			</div>
			<div class="hidden md:block lg:w-2/12">
				<Dropdown 
					v-if="ticketTypes"
					placement="left" 
					:options="typesAsDropdownOptions()" 
					:dropdown-width-full="true"
				>
					<template v-slot="{ toggleTypes }">
						<div  
							class="w-full cursor-pointer"
							@click="toggleTypes"
						>
							<div v-if="ticket.ticket_type" class="flex items-center w-40">
								<div class="text-gray-500 truncate"> {{ ticket.ticket_type }} </div>
								<FeatherIcon class="w-2 h-2  ml-1 hidden group-hover:block" name="chevron-down"/>
							</div>
							<div v-else class="hidden group-hover:block">
								<span class="text-base text-gray-400"> set type </span>
							</div>
						</div>
					</template>
				</Dropdown>
			</div>
			<div class="sm:w-2/12">
				<div 
					v-if="getResolutionDueIn()" 
					:color="getResolutionBadgeColor()"
				>
					{{ getResolutionDueIn() }}
				</div>
			</div>
			<div class="sm:w-2/12">
			<Dropdown
					v-if="ticketStatuses"
					placement="left" 
					:options="statusesAsDropdownOptions()" 
					:dropdown-width-full="true"
				>
					<template v-slot="{ toggleStatuses }">
						<div class="w-full">
							<div 
								v-if="ticket.status"
								@click="toggleStatuses"	
								class="flex items-center"
							>
								<Badge :color="getBadgeColorBasedOnStatus(ticket.status)">
									<div class="cursor-pointer">{{ ticket.status }}</div>
								</Badge>
							</div>
							<div v-else class="hidden group-hover:block">
								<span class="text-base text-gray-400"> set status </span>
							</div>
						</div>
					</template>
				</Dropdown>
			</div>
			<div class="sm:w-1/12">
				<div class="flex sm:pl-0 md:pl-3 items-center">
					<div class="sm:w-4/12">
						<div class="hidden text-gray-600 sm:block">
							<div>
								{{ $dayjs.shortFormating($dayjs(ticket.modified).fromNow()) }}
							</div>
						</div>
					</div>
					<div class="sm:w-8/12">
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
											<Avatar class="sm" :label="assignee.agent_name" :imageURL="assignee.image" />
										</div>
									</div>
									<div v-else class="hidden group-hover:block">
										<span class="text-base text-gray-400"> assign </span>
									</div>
								</div>
							</template>
						</Dropdown>
					</div>
				</div>
			</div>
			
			<!-- <div
				class="mr-4"
			>
				<Input type="checkbox" value="" />
			</div>
			<router-link 
				:to="`/helpdesk/tickets/${ticket.name}`"
				class="sm:w-9/12"
			>
				<div class="flex flex-col space-y-1">
					<div class="flex items-center">
					</div>
					<div class="flex items-center" v-if="ticket.contact">
						<div class="flex">
							<FeatherIcon class="w-4 h-4 stroke-slate-400" name="user" />
							<div class="ml-1 text-base">{{ ticket.contact.name }}</div>
						</div>
					</div>
				</div>
			</router-link>
			<div class="flex items-center justify-between sm:justify-start font-light sm:w-6/12">
				<div class="hidden sm:w-1/12 text-base text-gray-600 sm:block">
					<div class="flex items-center">
						<div>
							<FeatherIcon class="w-3 h-3 stroke-slate-400" name="edit-2"/>
						</div>
						<div class="ml-1">
							{{ $dayjs(ticket.modified).fromNow() }}
						</div>
					</div>
				</div>
			</div>
			<div class="sm:w-1/12">
			</div> -->
		</div>
		<div class="transform translate-y-2"/>
	</div>
</template>

<script>
import { Badge, Dropdown, Input, FeatherIcon, Avatar } from 'frappe-ui'
import { inject } from '@vue/runtime-core'

export default {
	name: 'TicketListItem',
	props: ['ticketId'],
	components: {
		Input,
		Badge,
		Dropdown,
		FeatherIcon,
		Avatar
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

		return {
			user,
			
			tickets,
			ticketTypes,
			ticketPriorities,
			ticketStatuses,

			agents,

			ticketController
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
				return 'red'
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
			let typeItems = [];
			if (this.ticketPriorities) {
				this.ticketPriorities.forEach(priority => {
					typeItems.push({
						label: priority.name,
						handler: () => {
							this.ticketController.set(this.ticketId, 'priority', priority.name)
						},
					});
				});
				return typeItems;
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
			let resolutionString = this.$dayjs().to(resolutionBy);
			if (["Resolution Due"].includes(agreementStatus)) {
				return this.ticket.resolution_by ? resolutionString : ''
			}
			return resolutionString;
		},
		getResolutionBadgeColor() {
			let resolutionDueIn = this.getResolutionDueIn()
			switch (resolutionDueIn) {
				case "Fulfilled":
					return "green"
				case "Overdue":
					return "red"
				default:
					return ""
			}
		}
	}
}
</script>

<style>

</style>