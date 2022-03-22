<template>
	<div>
		<div>
			<div
				v-if="sortedTickets"
				class="w-full pl-4 pr-8"
			>
				<div class="border-b pb-3 group flex items-center font-light text-base text-slate-500">
					<div class="mr-4 sm:w-6/12 flex space-x-2">
						<Input type="checkbox" @click="toggleSelectAllTickets()" :checked="allTicketsSelected" class="cursor-pointer" />
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
					<div v-for="ticket in sortedTickets" :key="ticket.name">
						<div>
							<TicketListItem :ticketId="ticket.name" @toggle-select="toggleTicketSelect(ticket.name)" :selected="selectedTickets.find(item => item == ticket.name)"/>
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
import { inject, ref } from 'vue'

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

		const selectedTickets = ref([])

		return { user, viewportWidth, tickets, selectedTickets }
	},
	computed: {
		filteredTickets() {
			let tickets = this.tickets
			let filteredTickets = []

			if (tickets) {
				filteredTickets = tickets
				for (let index in this.filters) {
					let filter = this.filters[index] 
					filteredTickets = Object.values(filteredTickets).filter((ticket) => {
						let filterFieldName = Object.keys(filter)[0]
						let filterValue = Object.values(filter)[0]
						switch(filterFieldName) {
							case 'assignee':
								return Object.values(ticket.assignees).find((assignee) => { 
									return (assignee.name == filterValue)
								})
							case 'raised_by':
								if (ticket.contact) {
									return ticket.contact.name == filterValue
								}
								return false
							default:
								return ticket[filterFieldName] == filterValue
						}
					})
				}
			}
			return filteredTickets
		},
		sortedTickets() {
			return this.getSortedTickets(this.filteredTickets)
		},
		allTicketsSelected() {
			return this.selectedTickets.length == Object.keys(this.sortedTickets).length
		}
	},
	watch: {
		selectedTickets(newValue) {
			this.$emit('selectedTicketsOnChange', newValue)
		}
	},
	methods: {
		getSortedTickets(tickets) {
			if (tickets && Object.keys(tickets).length > 0) {
				if (this.sortby) {
					tickets = Object.values(tickets).sort((a, b) => {
						return new Date(a[this.sortby]) - new Date(b[this.sortby]) * (this.sortDirection == 'assending' ? 1 : -1)
					})
					// update selected tickets
					this.selectedTickets = this.selectedTickets.filter((item1) => {
						return tickets.find((item2) => item2.name === item1)
					})
				}
				return tickets
			} else {
				return null
			}
		},
		toggleTicketSelect(ticketId) {
			if (this.selectedTickets.find((item) => item == ticketId)) {
				this.selectedTickets = this.selectedTickets.filter((item) => item != ticketId )
			} else {
				this.selectedTickets.push(ticketId)
			}
		},
		toggleSelectAllTickets() {
			this.selectedTickets = this.allTicketsSelected ? [] : this.sortedTickets.map((ticket) => ticket.name)
		}
	}
}
</script>
