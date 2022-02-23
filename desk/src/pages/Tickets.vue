<template>
	<div>
		<div class="flow-root border-b pt-2 pb-3 pr-8">
			<div class="float-left ml-4">
				<div class="flex items-center space-x-4">
					<Input type="checkbox" value="" />
					<Button icon-left="plus" appearance="primary" @click="() => {showNewTicketDialog = true}">Add Ticket</Button>
				</div>
			</div>
			<div class="float-right">
				<Button icon-left="filter" type="white">Filter</Button>
			</div>
		</div>
		<div v-if="tickets">
			<TicketList :tickets="tickets" />
		</div>
		<NewTicketDialog v-model="showNewTicketDialog" @ticket-created="() => {showNewTicketDialog=false}"/>
	</div>
</template>
<script>
import { Input } from 'frappe-ui'
import TicketList from '../components/tickets/TicketList.vue'
import NewTicketDialog from '../components/tickets/NewTicketDialog.vue'

export default {
	name: 'Tickets',
	inject: ['viewportWidth'],
	components: {
		TicketList,
		Input,
		NewTicketDialog
	},
	provide: {
		types: [],
		priorities: [],
		statuses: [],
		agents: []
	},
	data() {
		return {
			showNewTicketDialog: false
		}
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
			return this.$resources.tickets.data || null
		},
		agents() {
			return this.$resources.agents.data || null;
		},
		types() {
			return this.$resources.types.data || null
		},
		statuses() {
			return this.$resources.statuses.data || null;
		},
		priorities() {
			return this.$resources.priorities.data || null;
		}
	},
	mounted() {
		},
	activated() {
		this.$socket.on('list_update', (data) => {
			if (data['doctype'] == 'Ticket') {
				this.$resources.tickets.fetch()
			}
		});
		this.$currentPage.set('Tickets')
        console.log('tickets activated')
	},
	deactivated() {
		this.$socket.off('list_update');
	},
}
</script>
