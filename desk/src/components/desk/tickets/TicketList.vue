<template>
	<div>
		<div>
			<div
				v-if="filteredTickets"
				class="w-full block overflow-auto"
				:style="{ height: viewportWidth > 768 ? 'calc(100vh - 7.3rem)' : null }"
			>
				<div class="flex-auto" v-for="ticket in filteredTickets" :key="ticket.name">
					<div class="block px-0">
						<TicketListItem :ticketId="ticket.name" />
					</div>
				</div>
			</div>
		</div>
	</div>
</template>

<script>
import { Input } from 'frappe-ui'
import TicketListItem from './TicketListItem.vue'
import { inject } from 'vue'

export default {
	name: 'TicketList',
	components: {
		Input,
		TicketListItem
	},
	setup() {
		const viewportWidth = inject('viewportWidth')
		const tickets = inject('tickets')

		return { viewportWidth, tickets }
	},
	computed: {
		filteredTickets() {
			let tickets = this.tickets
			let filter = this.$ticketFilter.get()

			let filteredTickets = []

			if (filter == "Assigned to me") {
				for (let i in tickets) {
					if (tickets[i].assignees.length > 0) {
						for (let j = 0; j < tickets[i].assignees.length; j++) {
							if (tickets[i].assignees[j].name == this.$user.get().agent.name) {
								filteredTickets.push(tickets[i])
							}
						}
					}
				}
			} else {
				filteredTickets = tickets
			}

			return filteredTickets;
		}
	}
}
</script>
