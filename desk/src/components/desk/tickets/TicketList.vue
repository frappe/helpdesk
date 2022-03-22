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

		return { user, viewportWidth, tickets }
	},
	computed: {
		filteredTickets() {
			let tickets = this.tickets
			let filteredTickets = []

			if (tickets) {
				filteredTickets = tickets
				for (let key in this.filters) {
					filteredTickets = Object.values(filteredTickets).filter((ticket) => {
						switch(key) {
							case 'assignee':
								return Object.values(ticket.assignees).find((assignee) => { 
									return (assignee.name == this.filters[key])
								})
							default:
								return ticket[key] == this.filters[key]
						}
						return true
					})
				}
			}
			return filteredTickets
		}
	},
	methods: {
		sortedTickets(tickets) {
			if (tickets && Object.keys(tickets).length > 0) {
				if (this.sortby) {
					return Object.values(tickets).sort((a, b) => {
						return new Date(a[this.sortby]) - new Date(b[this.sortby]) * (this.sortDirection == 'assending' ? 1 : -1)
					})
				} else {
					return tickets
				}
			} else {
				return null
			}
		}
	}
}
</script>
