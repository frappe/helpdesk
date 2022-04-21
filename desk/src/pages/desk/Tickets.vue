<template>
	<div>
		<div class="flow-root pt-3 pb-5 pr-8 pl-4">
			<div class="float-left">
			</div>
			<div class="float-right">
				<!-- TODO: add v-on-outside-click="() => { toggleFilters = false }" -->
				<div v-if="showTicketBluckUpdatePanel" class="flex space-x-3">
					<Button @click="markSelectedTicketsAsClosed()">Mark as Closed</Button>
					<Dropdown
						v-if="agents"
						placement="right" 
						:options="agentsAsDropdownOptions()" 
						:dropdown-width-full="true"
						class="text-base flex flex-row-reverse"
					>
						<template v-slot="{ toggleAssignees }">
							<div @click="toggleAssignees" class="cursor-pointer">
								<Button appearance="secondary">
									<div class="flex items-center space-x-2">
										<div>Assign</div>
										<CustomIcons class="h-4" name="select" />
									</div>
								</Button>
							</div>
						</template>
					</Dropdown>
				</div>
				<div v-else class="flex space-x-3">
					<FilterBox class="mt-10" v-if="toggleFilters" @close="() => { toggleFilters = false }" :options="getFilterBoxOptions()" v-model="filters"/>
					<Button :class="Object.keys(filters).length == 0 ? 'bg-gray-100 text-gray-600' : 'bg-blue-100 text-blue-500 hover:bg-blue-300'" @click="() => { toggleFilters = !toggleFilters }">
						<div class="flex items-center space-x-2">
							<CustomIcons height="18" width="18" name="filter" :class="Object.keys(filters).length > 0 ? 'stroke-blue-600' : 'stroke-black'" />
							<div>Add Filters</div>
							<div class="bg-blue-500 text-white px-1.5 rounded" v-if="Object.keys(filters).length > 0">{{ Object.keys(this.filters).length }}</div>
						</div>
					</Button>
					<Button icon-left="plus" appearance="primary" @click="() => {showNewTicketDialog = true}">Add Ticket</Button>
				</div>
			</div>
		</div>
		<TicketList :sortby="sortby" :sortDirection="sortDirection" :filters="filters" @selected-tickets-on-change="triggerSelectedTickets" />
		<NewTicketDialog v-model="showNewTicketDialog" @ticket-created="() => {showNewTicketDialog = false}"/>
	</div>
</template>
<script>
import { Input, Dropdown, FeatherIcon } from 'frappe-ui'
import TicketList from '@/components/desk/tickets/TicketList.vue'
import NewTicketDialog from '@/components/desk/tickets/NewTicketDialog.vue'
import CustomIcons from '@/components/desk/global/CustomIcons.vue'
import FilterBox from '@/components/desk/global/FilterBox.vue'
import { inject, ref } from 'vue'

export default {
	name: 'Tickets',
	components: {
		TicketList,
		Input,
		NewTicketDialog,
		CustomIcons,
		Dropdown,
		FeatherIcon,
		FilterBox
	},
	setup() {
		const user = inject('user')
		const tickets = inject('tickets')
		const ticketFilter = inject('ticketFilter')
		const showNewTicketDialog = ref(false)

		const filters = ref([])
		const toggleFilters = ref(false)

		const ticketTypes = inject('ticketTypes')
		const ticketPriorities = inject('ticketPriorities')
		const ticketStatuses = inject('ticketStatuses')
		const agents = inject('agents')
		const contacts = inject('contacts')
		
		const sortby = ref('modified')
		const sortDirection = ref('dessending')

		const selectedTickets = ref([])

		const ticketController = inject('ticketController')

		return {
			user, 
			tickets, 
			ticketFilter, 
			showNewTicketDialog, 
			filters, 
			sortby, 
			sortDirection, 
			toggleFilters,
			ticketTypes,
			ticketPriorities,
			ticketStatuses,
			agents,
			contacts,
			selectedTickets,
			ticketController
		}
	},
	mounted() {
		this.syncFilterBasedOnTicketFilter(this.ticketFilter)
	},
	computed: {
		showTicketBluckUpdatePanel() {
			return this.selectedTickets.length > 0
		}
	},
	watch: {
		ticketFilter(newValue) {
			this.syncFilterBasedOnTicketFilter(newValue)
		},
		filters(newValue) {
			let filter = newValue.find(x => Object.keys(x)[0] === 'assignee')
			if (filter && this.user.agent) {
				if (Object.values(filter)[0] === this.user.agent.name) {
					this.ticketFilter = "Assigned Tickets"
				} else {
					this.ticketFilter = "All Tickets"
				}
			} else {
				this.ticketFilter = "All Tickets"
			}
		}
	},
	methods: {
		syncFilterBasedOnTicketFilter(newTicketFilterValue) {
			this.filters = this.filters.filter(x => Object.keys(x)[0] != 'assignee')
			switch(newTicketFilterValue) {
				case 'Assigned Tickets':
					this.filters.push({assignee: this.user.agent.name})
					break;
			}
		},
		toggleSort(sortby) {
			if (this.sortby != sortby) {
				this.sortDirection = 'assending'
				this.sortby = sortby
			} else {
				this.sortDirection = (this.sortDirection == 'assending' ? 'dessending' : 'assending')
			}
		},
		getFilterBoxOptions() {
			return [
				{label: "Type", name: "ticket_type", items: this.ticketTypes.map((item) => item.name)},
				{label: "Contact", name: "raised_by", items: this.contacts.map((item) => item.name)},
				{label: "Status", name: "status", items: this.ticketStatuses},
				{label: "Assignee", name: "assignee", items: this.agents.map((item) => item.name)},
				{label: "Priority", name: "priority", items: this.ticketPriorities.map((item) => item.name)},
				// TODO: {label: "Created On", name: "creation", type: 'calander'}
			]
		},
		triggerSelectedTickets(selectedTickets) {
			this.selectedTickets = selectedTickets
		},
		markSelectedTicketsAsClosed() {
			if (this.selectedTickets) {
				this.ticketController.bulkSet(this.selectedTickets, 'status', 'Closed')
			}
		},
		agentsAsDropdownOptions() {
			let agentItems = [];
			if (this.agents) {
				this.agents.forEach(agent => {
					agentItems.push({
						label: agent.agent_name,
						handler: () => {
							if (this.selectedTickets) {
								this.ticketController.bulkSet(this.selectedTickets, 'agent', agent.name)
							}
						},
					});
				});
				let options = [];
				if (this.user.agent) {
					options.push({
						group: 'Myself',
						hideLabel: true,
						items: [
							{
								label: 'Assign to me',
								handler: () => {
									if (this.selectedTickets) {
										this.ticketController.bulkSet(this.selectedTickets, 'agent')
									}
								}
							},
						],
					})
				}
				options.push({
					group: 'All Agents',
					hideLabel: true,
					items: agentItems,
				})
				return options;
			} else {
				return null;
			}
		},
	}
}

// TODO: transfer the tickets controllers to desk.vue file
</script>
