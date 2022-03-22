<template>
	<div>
		<div>
			<div
				v-if="filteredTickets"
				class="w-full pl-4 pr-8"
			>
				<div class="border-b pb-3 group flex items-center font-light text-base text-slate-500">
					<div class="mr-4 sm:w-6/12 flex space-x-2">
						<Input type="checkbox" value="" />
						<div class="grow">Subject</div>
					</div>
					<div class="hidden md:block lg:w-2/12">Raised By</div>
					<div class="hidden md:block lg:w-2/12">Type</div>
					<div class="sm:w-2/12">Due</div>
					<div class="sm:w-2/12">Status</div>
					<div class="sm:w-1/12"></div>
				</div>
				<div 
					class="block overflow-auto"
					:style="{ height: viewportWidth > 768 ? 'calc(100vh - 9.4rem)' : null }"
				>
					<div v-for="ticket in sortedTickets(filteredTickets)" :key="ticket.name">
						<div>
							<TicketListItem :ticketId="ticket.name" />
						</div>
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
	props: ['sortby', 'sortDirection', 'filters'],
	components: {
		Input,
		TicketListItem
	},
	setup() {
		const user = inject('user')

		const viewportWidth = inject('viewportWidth')
		const tickets = inject('tickets')
		const ticketFilter = inject('ticketFilter')

		return { user, viewportWidth, tickets, ticketFilter }
	},
	computed: {
		filteredTickets() {
			let tickets = this.tickets
			let filter = this.ticketFilter

			let filteredTickets = []

			if (filter == "Assigned to me") {
				for (let i in tickets) {
					if (tickets[i].assignees.length > 0) {
						for (let j = 0; j < tickets[i].assignees.length; j++) {
							if (tickets[i].assignees[j].name == this.user.agent.name) {
								filteredTickets.push(tickets[i])
							}
						}
					}
				}
			} else {
				filteredTickets = tickets
			}

			console.log(Object.keys(filteredTickets).length)

			return filteredTickets;
		}
	},
	methods: {
		sortedTickets(tickets) {
			if (tickets && Object.keys(tickets).length > 0) {
				switch(this.sortby) {
					case 'last modified':
						return Object.values(tickets).sort((a, b) => {
							return new Date(a.modified) - new Date(b.modified) * (this.sortDirection == 'assending' ? 1 : -1)
						})
					default:
						return tickets
				}
			} else {
				return null
			}
		}
	}
}
</script>
