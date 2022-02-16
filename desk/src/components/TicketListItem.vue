<template>
	<div class="block py-4 hover:bg-gray-50 border-b">
		<div 
			v-if="ticketDetails"
			class="group flex items-center justify-between sm:justify-start font-light px-4"
		>
			<div
				class="mr-4"
			>
				<Input type="checkbox" value="" />
			</div>
			<a 
				:href="'ticket/' + ticketDetails.name"
				class="sm:w-6/12"
			>
				<div class="flex flex-col space-y-1">
					<div class="flex items-center">
						<div class="text-xl font-medium">{{ ticketDetails.subject }}</div>
						<div class="ml-1 text-base text-slate-400">#{{ ticketDetails.name }}</div>
					</div>
					<div class="flex items-center">
						<div class="flex">
							<FeatherIcon class="w-4 h-4 stroke-slate-400" name="user" />
							<div class="ml-1 text-base">{{ ticketDetails.contact }}</div>
						</div>
					</div>
				</div>
			</a>
			<Dropdown
				v-if="this.statuses"
				placement="left" 
				:options="statusesAsDropdownOptions()" 
				:dropdown-width-full="true"
				class="text-base sm:w-1/12"
			>
				<template v-slot="{ toggleStatuses }">
					<div class="w-full cursor-pointer">
						<div 
							v-if="ticket.status"
							@click="toggleStatuses"	
							class="flex items-center"
						>
							<FeatherIcon class="w-2 h-2 stroke-transparent" :class="getBadgeColorBasedOnStatus(ticketDetails.status)" name="circle"/>
							<div class="ml-1 text-gray-500">{{ ticketDetails.status }}</div>
						</div>
						<div v-else class="hidden group-hover:block">
							<span class="text-sm text-gray-400"> set status </span>
						</div>
					</div>
				</template>
			</Dropdown>
			<div class="hidden sm:w-2/12 text-sm text-gray-600 sm:block">
				<div class="flex items-center">
					<div>
						<FeatherIcon class="w-3 h-3 stroke-slate-400" name="edit-2"/>
					</div>
					<div class="ml-1">
						{{ $dayjs(ticketDetails.modified).fromNow() }}
					</div>
				</div>
			</div>
			<Dropdown 
				v-if="this.types"
				placement="left" 
				:options="typesAsDropdownOptions()" 
				:dropdown-width-full="true"
				class="text-base sm:w-2/12"
			>
				<template v-slot="{ toggleTypes }">
					<div  
						class="w-full"
						@click="toggleTypes"
					>
						<div v-if="ticketDetails.ticket_type" class="flex items-center">
							<div>
								<FeatherIcon class="w-3 h-3 stroke-slate-400" name="tag" />
							</div>
							<div class="ml-1 text-gray-500">
								{{ ticketDetails.ticket_type }}
							</div>
						</div>
						<div v-else class="hidden group-hover:block">
							<span class="text-sm text-gray-400"> set type </span>
						</div>
					</div>
				</template>
			</Dropdown>
			<div class="hidden sm:w-1/12 text-sm text-gray-600 sm:block">
				<div class="flex items-center">
					<div>
						<FeatherIcon class="w-3 h-3 stroke-slate-400" name="shield"/>
					</div>
					<div class="ml-1">
						Due in 3h
					</div>
				</div>
			</div> 
			<Dropdown
				v-if="this.agents"
				placement="right" 
				:options="agentsAsDropdownOptions()" 
				:dropdown-width-full="true"
				class="text-base sm:w-1/12 flex flex-row-reverse"
			>
				<template v-slot="{ toggleAssignees }">
					<div  
						class="w-full"
						@click="toggleAssignees"
					>
						<div v-if="ticketDetails.assignee">
							<Avatar class="w-4 h-4" label="John Doe" :imageURL="ticketDetails.assingee_image" />
						</div>
						<div v-else class="hidden group-hover:block">
							<span class="text-sm text-gray-400"> assign agent </span>
						</div>
					</div>
				</template>
			</Dropdown>
		</div>
		<div class="transform translate-y-2"/>
	</div>
</template>

<script>
import { Badge, Dropdown, Input, FeatherIcon, Avatar } from 'frappe-ui'

export default {
	name: 'TicketListItem',
	props: ['ticket', 'agents', 'types', 'statuses'],
	components: {
		Input,
		Badge,
		Dropdown,
		FeatherIcon,
		Avatar
	},
	data() {
		return {
			ticketDetailsRefreshed: false,
			localTicket: null,
		}
	},
	resources: {
		ticket() {
			return {
				method: 'helpdesk.api.ticket.get_ticket',
				params: {
					ticket_id: this.ticketDetails.name
				},
				onSuccess: () => {
					this.ticketDetailsRefreshed = true;
				}
			}
		},
		assignTicketToAgent() {
			return {
				method: 'helpdesk.api.ticket.assign_ticket_to_agent',
				debounce: 300,
				onSuccess: () => {
					this.$resources.ticket.fetch();
				}
			}
		},
		assignTicketType() {
			return {
				method: 'helpdesk.api.ticket.assign_ticket_type',
				debounce: 300,
				onSuccess: () => {
					this.$resources.ticket.fetch();
				}
			}
		},
		assignTicketStatus() {
			return {
				method: 'helpdesk.api.ticket.assign_ticket_status',
				debounce: 300,
				onSuccess: () => {
					this.$resources.ticket.fetch();
				}
			}
		},
	},
	computed: {
		ticketDetails() {
			if (this.ticketDetailsRefreshed) {
				this.ticketDetailsRefreshed = false;
				this.localTicket = this.$resources.ticket.data ? this.$resources.ticket.data : this.ticket;
			} else {
				this.localTicket = this.ticket;
			}
			return this.localTicket;
		},
	},
	methods: {
		getBadgeColorBasedOnStatus(status) {
			if (['Open'].includes(status)) {
				return 'fill-green-500'
			}
			if (['Closed', 'Resolved'].includes(status)) {
				return 'fill-red-500'
			}
			if (['Replied'].includes(status)) {
				return 'fill-yellow-500'
			}
			if (['On Hold'].includes(status)) {
				return 'fill-blue-500'
			}
		},
		agentsAsDropdownOptions() {
			let agentItems = [];
			if (this.agents) {
				this.agents.forEach(agent => {
					agentItems.push({
						label: agent.agent_name,
						handler: () => {
							this.$resources.assignTicketToAgent.submit({
								ticket_id: this.ticketDetails.name,
								agent_id: agent.name
							});
						},
					});
				});
				let options = [
					{
						group: 'Actions',
						hideLabel: true,
						items: [
							{
								label: 'Assign to me',
								handler: () => {
									this.$resources.assignTicketToAgent.submit({
										ticket_id: this.ticketDetails.name
									});
								}
							},
						],
					},
					{
						items: agentItems,
					}
				];
				return options;
			} else {
				return null;
			}
		},
		typesAsDropdownOptions() {
			let typeItems = [];
			if (this.types) {
				this.types.forEach(type => {
					typeItems.push({
						label: type,
						handler: () => {
							this.$resources.assignTicketType.submit({
								ticket_id: this.ticketDetails.name,
								type: type
							});
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
			if (this.statuses) {
				this.statuses.forEach(status => {
					statusItems.push({
						label: status,
						handler: () => {
							this.$resources.assignTicketStatus.submit({
								ticket_id: this.ticketDetails.name,
								status: status
							});
						},
					});
				});
				return statusItems;
			} else {
				return null;
			}
		}
	}
}
</script>

<style>

</style>