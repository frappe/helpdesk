<template>
	<div>
		<div class="w-full select-none">
			<div class="bg-[#F7F7F7] group flex items-center font-light text-base text-slate-500 py-[10px] pl-[11px] pr-[49.80px] rounded-[6px]">
				<Input 
					type="checkbox" 
					@click="toggleSelectAllTickets()" 
					:checked="allTicketsSelected" 
					class="cursor-pointer mr-2 hover:visible" 
					:class="allTicketsSelected ? 'visible' : 'invisible'" 
				/>
				<div class="sm:w-1/12 flex items-baseline space-x-[7px] cursor-pointer" @click="toggleSort('name')">
					<span>#</span>
					<CustomIcons 
						class="h-[6px] fill-gray-400 stroke-transparent" 
					/>
				</div>
				<div class="sm:w-8/12 flex items-baseline space-x-[6px] cursor-pointer" @click="toggleSort('subject')">
					<span>Subject</span>
					<CustomIcons 
						class="h-[6px] fill-gray-400 stroke-transparent" 
					/>
				</div>
				<div class="sm:w-2/12 flex items-baseline space-x-[6px] cursor-pointer" @click="toggleSort('status')">
					<span>Status</span>
					<CustomIcons 
						class="h-[6px] fill-gray-400 stroke-transparent" 
					/>
				</div>
				<div class="sm:w-3/12 flex items-baseline space-x-[6px] cursor-pointer" @click="toggleSort('rasied_by')">
					<span>Created By</span>
					<CustomIcons 
						class="h-[6px] fill-gray-400 stroke-transparent"
					/>
				</div>
				<div class="sm:w-2/12 flex items-baseline space-x-[6px] cursor-pointer" @click="toggleSort('resolution_by')">
					<span>Due In</span>
					<CustomIcons 
						class="h-[6px] fill-gray-400 stroke-transparent" 
					/>
				</div>
				<div class="sm:w-1/12 flex items-baseline space-x-[6px] cursor-pointer" @click="toggleSort('modified')">
					<span>Modified</span>
					<CustomIcons 
						class="h-[6px] fill-gray-400 stroke-transparent" 
					/>
				</div>
			</div>
			<div v-if="tickets">
				<div 
					v-if="sortedTickets"
					class="block overflow-auto"
					:style="{ height: viewportWidth > 768 ? 'calc(100vh - 7rem)' : null }"
				>
					<div v-if="sortedTickets.length > 0">
						<div class="space-y-[2px]">
							<div v-for="ticket in sortedTickets" :key="ticket.name">
								<div>
									<TicketListItem :ticketId="ticket.name" @toggle-select="toggleTicketSelect(ticket.name)" :selected="selectedTickets.find(item => item == ticket.name)"/>
								</div>
							</div>
						</div>
					</div>
					<div v-else>
						<div class="grid place-content-center h-48 w-full">
							<div>
								<CustomIcons name="empty-list" class="h-12 w-12 mx-auto mb-2" />
								<div class="text-gray-500 mb-2">No tickets found</div>
							</div>
						</div>
					</div>
				</div>
			</div>
			<div v-else class="py-5">
				<LoadingText text="Fetching tickets..." />
			</div>
		</div>
	</div>
</template>

<script>
import { Input, LoadingText } from 'frappe-ui'
import CustomIcons from '@/components/desk/global/CustomIcons.vue'
import TicketListItem from './TicketListItem.vue'
import { inject, ref } from 'vue'

export default {
	name: 'TicketList',
	props: ['filters'],
	components: {
		Input,
		LoadingText,
		CustomIcons,
		TicketListItem
	},
	setup() {
		const user = inject('user')

		const viewportWidth = inject('viewportWidth')
		const tickets = inject('tickets')

		const selectedTickets = ref([])

		const sortby = ref('modified')
		const sortDirection = ref('dessending')

		return { user, viewportWidth, tickets, selectedTickets, sortby, sortDirection }
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
				if (this.user.agent) {
					switch(this.$route.query.menu_filter) {
						case 'unassigned':
							filteredTickets = Object.values(filteredTickets).filter((ticket) => {
								if (Object.keys(ticket.assignees).length > 0) {
									return Object.values(ticket.assignees).find((assignee) => { 
										return (assignee.name != this.user.agent.name)
									})
								} else {
									return true
								}
							})
							break
						case 'assigned-to-me':
							filteredTickets = Object.values(filteredTickets).filter((ticket) => {
								return Object.values(ticket.assignees).find((assignee) => { 
									return (assignee.name == this.user.agent.name)
								})
							})
							break
					}
				}
				if (this.$route.query.menu_filter == 'unassigned' && this.user.agent) {
				}
			}
			return filteredTickets
		},
		sortedTickets() {
			return this.getSortedTickets(this.filteredTickets)
		},
		allTicketsSelected() {
			return (this.selectedTickets.length == Object.keys(this.sortedTickets).length) && (Object.keys(this.sortedTickets).length > 0)
		}
	},
	watch: {
		selectedTickets(newValue) {
			this.$emit('selectedTicketsOnChange', newValue)
		}
	},
	methods: {
		toggleSort(sortby) {
			// TODO: once sorting is fixed remove the return
			return
			if (this.sortby != sortby) {
				this.sortDirection = 'assending'
				this.sortby = sortby
			} else {
				this.sortDirection = (this.sortDirection == 'assending' ? 'dessending' : 'assending')
			}
		},
		getSortedTickets(tickets) {
			if (tickets) {
				if (Object.keys(tickets).length > 0) {
					if (this.sortby) {
						tickets = Object.values(tickets).sort((a, b) => {
							return (new Date(a[this.sortby]) - new Date(b[this.sortby])) * (this.sortDirection == 'assending' ? 1 : -1)
						})
						// update selected tickets
						this.selectedTickets = this.selectedTickets.filter((item1) => {
							return tickets.find((item2) => item2.name === item1)
						})
					}
					return tickets
				} else {
					return []
				}
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
