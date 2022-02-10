<template>
	<div>
		<div>
			<div class="flow-root mb-2">
				<p class="float-left text-6xl font-bold"> Tickets </p>
				<div class="float-right mb-4">
					<div class="flex space-x-3">
						<Button icon-left="filter">Add Filter</Button>
						<Button icon-left="plus">Last Modified</Button>
						<Button icon-left="plus" type="primary">Add Ticket</Button>
					</div>
				</div>
			</div>
			<div v-if="tickets">
				<TicketList :ticketList="tickets" :agents="agents"/>
			</div>
		</div>
	</div>
</template>
<script>
import TicketList from './TicketList.vue'

export default {
	name: 'Tickets',
	inject: ['viewportWidth'],
	components: {
		TicketList
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
		}
	},
	computed: {
		tickets() {
			return this.$resources.tickets.data ? this.$resources.tickets.data : null
		},
		agents() {
			return this.$resources.agents.data ? this.$resources.agents.data : null;
		}
	},
}
</script>
