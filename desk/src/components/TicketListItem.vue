<template>
	<div class="block rounded-md sm:px-2 hover:bg-gray-50">
		<div 
			v-if="ticket"
			class="group flex items-center justify-between sm:justify-start font-light"
		>
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
				:options="agentsAsDropdownOptions()" 
				:dropdown-width-full="true"
				class="text-base sm:w-3/12"
			>
				<template v-slot="{ toggleAssignees }">
					<div  
						class="w-full"
						@click="toggleAssignees"
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
</template>

<script>
import { Badge, Dropdown, Input } from 'frappe-ui'

export default {
	name: 'TicketListItem',
	props: ['ticketName', 'agents'],
	components: {
		Input,
		Badge,
		Dropdown
	},
	resources: {
		ticket() {
			return {
				method: 'helpdesk.api.ticket.get_ticket',
				params: {
					ticket_id: this.ticketName
				},
				auto: true
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
		}
	},
	computed: {
		ticket() {
			return this.$resources.ticket.data ? this.$resources.ticket.data : null
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
				return 'orange'
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
								ticket_id: this.ticketName,
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
										ticket_id: this.ticketName
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
	}
}
</script>

<style>

</style>