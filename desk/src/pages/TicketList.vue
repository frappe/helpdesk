<template>
	<div>
		<div class="sm:py-1 sm:border sm:border-gray-100 sm:rounded-md sm:shadow sm:px-2">
			<div class="block py-2 rounded-md sm:px-2">
				<div class="block py-1 rounded-md sm:px-2">
					<div class="flex items-center justify-between sm:justify-start font-light">
						<div class="mr-4">
							<Input type="checkbox" value="" />
						</div>
						<div class="text-base sm:w-5/12">
							Subject
						</div>
						<div class="text-base sm:w-3/12">
							Requester
						</div> 
						<div class="text-base sm:w-2/12">
							Type
						</div> 
						<div class="text-base sm:w-2/12">
							Status
						</div> 
						<div class="text-base sm:w-3/12">
							Assignee
						</div> 
						<div class="text-base sm:w-2/12">
							Updated
						</div> 
					</div>
				</div>
				<div class="transform translate-y-2 border-b-2"/>
			</div>
			<div 
				v-if="tickets"
				class="w-full block overflow-auto"
				:style="{ height: viewportWidth > 768 ? 'calc(100vh - 15rem)' : null }"
			>
				<div class="flex-auto" v-for="ticket in tickets" :key="ticket.name">
					<div class="block py-1 rounded-md sm:px-2">
						<div class="block rounded-md sm:px-2 hover:bg-gray-50">
							<div class="group flex items-center justify-between sm:justify-start font-light">
								<div 
									:href="'ticket/' + ticket.name"
									class="mr-4"
								>
									<Input type="checkbox" value="" />
								</div>
								<a 
									:href="'ticket/' + ticket.name"
									class="text-base sm:w-5/12"
								>
									{{ ticket.subject }}
								</a>
								<div class="text-base sm:w-3/12">
									{{ ticket.contact }}
								</div>
								<div class="text-base sm:w-2/12">
									{{ ticket.ticket_type }}
								</div> 
								<div class="text-base sm:w-2/12">
									<Badge :color="getBadgeColorBasedOnStatus(ticket.status)">{{ ticket.status }}</Badge>
								</div> 
								<Dropdown 
									v-if="agents"
									placement="left" 
									:options="agentsAsDropdownOptions" 
									:dropdown-width-full="true"
									class="text-base sm:w-3/12"
								>
									<template v-slot="{ toggleAssignees }">
										<div  
											class="w-full"
											@click="
												toggleAssignees;
												this.ticketClicked(ticket);
											"
										>
											<div v-if="ticket.assignee">
												{{ ticket.assignee }}
											</div>
											<div v-else class="hidden group-hover:block">
												<span class="text-sm text-gray-500"> Assign an agent </span>
											</div>
										</div>
									</template>
								</Dropdown>
								<div class="hidden sm:w-2/12 text-sm text-gray-600 sm:block">
									{{ ticket.modified }}
								</div> 
							</div>
							<div class="transform translate-y-2 border-b"/>
						</div>
					</div>
				</div>
			</div>
		</div>
	</div>
</template>

<script>
import { Input, Badge, Dropdown } from 'frappe-ui'

export default {
	name: 'TicketList',
	inject: ['viewportWidth'],
	data() {
		return {
			currentTicket: null
		}
	},
	components: {
		Input,
		Badge,
		Dropdown
	},
	resources: {
		tickets() {
			return {
				method: 'helpdesk.api.ticket.get_tickets',
				auto: true
			}
		},
		agents() {
			return {
				method: 'helpdesk.api.agent.get_all',
				auto: true
			}
		},
		assignTicketToAgent() {
			return {
				method: 'helpdesk.api.ticket.assign_ticket_to_agent',
				debounce: 300,
				onSuccess: () => {
					this.$resources.tickets.fetch();
				}
			}
		}
	},
	computed: {
		tickets() {
			return this.$resources.tickets.data ? this.$resources.tickets.data : null
		},
		agents() {
			return this.$resources.agents.data ? this.$resources.agents.data : null;
		},
		agentsAsDropdownOptions() {
			let agentItems = [];
			if (this.agents) {
				this.agents.forEach(agent => {
					agentItems.push({
						label: agent.agent_name,
						handler: () => {
							this.$resources.assignTicketToAgent.submit({
								ticket_id: this.currentTicket.name,
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
								label: 'Remove',
								icon: 'trash-2',
								handler: () => {
									this.$resources.assignTicketToAgent.submit({
										ticket_id: this.currentTicket.name
									});
								}
							},
						],
					},
					{
						group: 'Assign',
						items: agentItems,
					}
				];

				return options;
			} else {
				return null;
			}
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
				return 'orange'
			}
		},
		ticketClicked(ticket) {
			this.currentTicket = ticket;
		}
	}
}
</script>
