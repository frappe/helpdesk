<template>
	<div>
		<div>
			<div class="flow-root border-b pt-2 pb-3 pr-8">
				<div class="float-left ml-4">
					<div class="flex items-center space-x-4">
						<Input type="checkbox" value="" />
						<Button icon-left="plus" type="primary">Add Ticket</Button>
					</div>
				</div>
				<div class="float-right">
					<Button icon-left="filter" type="white">Filter</Button>
				</div>
			</div>
			<div v-if="tickets">
				<TicketList 
					:ticketList="tickets" 
					:agents="agents"
					:types="types"
					:statuses="statuses"
					:priorities="priorities"
				/>
			</div>
		</div>
	</div>
</template>
<script>
import TicketList from './TicketList.vue'
import { Input } from 'frappe-ui'

export default {
	name: 'Tickets',
	inject: ['viewportWidth'],
	components: {
		TicketList,
		Input
	},
	resources: {
		tickets() {
			return {
				method: 'helpdesk.api.ticket.get_tickets',
				params: {
					filter: this.$ticketFilter.get()
				},
				auto: true
			}
		},
		agents() {
			return {
				method: 'helpdesk.api.agent.get_all',
				auto: true
			}
		},
		types() {
			return {
				method: 'helpdesk.api.ticket.get_all_ticket_types',
				auto: true
			}
		},
		statuses() {
			return {
				method: 'helpdesk.api.ticket.get_all_ticket_statuses',
				auto: true
			}
		},
		priorities() {
			return {
				method: 'helpdesk.api.ticket.get_all_ticket_priorities',
				auto: true
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
		types() {
			return this.$resources.types.data ? this.$resources.types.data : null
		},
		statuses() {
			return this.$resources.statuses.data ? this.$resources.statuses.data : null;
		},
		priorities() {
			return this.$resources.priorities.data ? this.$resources.priorities.data : null;
		}
	},
}
</script>
