<template>
	<div class="block rounded-md sm:px-2 hover:bg-gray-50">
		<div 
			v-if="ticketDetails"
			class="group flex items-center justify-between sm:justify-start font-light"
		>
			<div
				class="mr-4"
			>
				<Input type="checkbox" value="" />
			</div>
			<a 
				:href="'ticket/' + ticketDetails.name"
				class="text-base sm:w-5/12"
			>
				{{ ticketDetails.subject }}
			</a>
			<div class="text-base sm:w-3/12">
				{{ ticketDetails.contact }}
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
						<div v-if="ticketDetails.ticket_type">
							{{ ticketDetails.ticket_type }}
						</div>
						<div v-else class="hidden group-hover:block">
							<span class="text-sm text-gray-500"> set type </span>
						</div>
					</div>
				</template>
			</Dropdown>
			<Dropdown
				v-if="this.statuses"
				placement="left" 
				:options="statusesAsDropdownOptions()" 
				:dropdown-width-full="true"
				class="text-base sm:w-2/12"
			>
				<template v-slot="{ toggleStatuses }">
					<div class="w-full cursor-pointer">
						<div 
							v-if="ticket.status"
							@click="toggleStatuses"	
						>
							<Badge 
								class="cursor-pointer"
								:color="getBadgeColorBasedOnStatus(ticketDetails.status)"
							>
								{{ ticketDetails.status }}
							</Badge>
						</div>
						<div v-else class="hidden group-hover:block">
							<span class="text-sm text-gray-500"> set status </span>
						</div>
					</div>
				</template>
			</Dropdown>
			<Dropdown
				v-if="this.agents"
				placement="left" 
				:options="agentsAsDropdownOptions()" 
				:dropdown-width-full="true"
				class="text-base sm:w-3/12"
			>
				<template v-slot="{ toggleAssignees }">
					<div  
						class="w-full"
						@click="toggleAssignees"
					>
						<div v-if="ticketDetails.assignee">
							{{ ticketDetails.assignee }}
						</div>
						<div v-else class="hidden group-hover:block">
							<span class="text-sm text-gray-500"> assign agent </span>
						</div>
					</div>
				</template>
			</Dropdown>
			<div class="hidden sm:w-2/12 text-sm text-gray-600 sm:block">
				{{ $dayjs(ticketDetails.modified).fromNow()}}
			</div> 
		</div>
		<div class="transform translate-y-2 border-b"/>
	</div>
</template>

<script>
import { Badge, Dropdown, Input } from 'frappe-ui'

export default {
	name: 'TicketListItem',
	props: ['ticket', 'agents', 'types', 'statuses'],
	components: {
		Input,
		Badge,
		Dropdown
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