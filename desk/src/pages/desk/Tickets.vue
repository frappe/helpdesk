<template>
	<div>
		<ListManager
			v-if="listManagerInitialised"
			class="px-[16px]"
			ref="ticketList"
			:options="{
				cache: ['Ticket', 'Desk'],
				doctype: 'Ticket',
				fields: [
					'priority', 
					'name', 
					'subject', 
					'ticket_type', 
					'status', 
					'contact', 
					'response_by', 
					'resolution_by', 
					'agreement_status', 
					'modified', 
					'_assign', 
					'_seen'
				],
				limit: 20,
				order_by: 'modified desc',
				filters: initialFilters,
				start_page: initialPage,
				route_query_pagination: true
			}"
		>
			<template #body="{ manager }">
				<div>
					<div class="flow-root py-[22px] h-[72px] px-[16px]">
						<div class="float-left">
						</div>
						<div class="float-right">
							<!-- TODO: add v-on-outside-click="() => { toggleFilters = false }" -->
							<div 
								v-if="Object.keys(manager.selectedItems).length > 0"
								class="flex space-x-3"
							>
								<Button :loading="$resources.bulkAssignTicketStatus.loading" @click="markSelectedTicketsAsClosed()">Mark as Closed</Button>
								<Dropdown
									v-if="agents"
									placement="right" 
									:options="agentsAsDropdownOptions()" 
									:dropdown-width-full="true"
								>
									<template v-slot="{ toggleAssignees }">
										<div class="flex flex-col">
											<Button :loading="$resources.bulkAssignTicketToAgent.loading" @click="toggleAssignees" class="cursor-pointer">
												<div class="flex items-center space-x-2">
													<div>Assign</div>
												</div>
											</Button>
										</div>
									</template>
								</Dropdown>
							</div>
							<div v-else class="flex items-center space-x-3">
								<div>
									<FilterBox class="mt-6" v-if="toggleFilters" @close="() => { toggleFilters = false }" :options="filterBoxOptions()" v-model="filters"/>
								</div>
								<div class="stroke-blue-500 fill-blue-500 w-0 h-0 block"></div>
								<Button :class="Object.keys(filters).length == 0 ? 'bg-gray-100 text-gray-600' : 'bg-blue-100 text-blue-500 hover:bg-blue-300'" @click="() => { toggleFilters = !toggleFilters }">
									<div class="flex items-center space-x-2">
										<CustomIcons height="18" width="18" name="filter" :class="Object.keys(filters).length > 0 ? 'stroke-blue-500 fill-blue-500' : 'stroke-black'" />
										<div>Add Filters</div>
										<div class="bg-blue-500 text-white px-1.5 rounded" v-if="Object.keys(filters).length > 0">{{ Object.keys(this.filters).length }}</div>
									</div>
								</Button>
								<Button icon-left="plus" appearance="primary" @click="() => {showNewTicketDialog = true}">Add Ticket</Button>
							</div>
						</div>
					</div>
					<TicketList :manager="manager" />
				</div>
			</template>
		</ListManager>
		<NewTicketDialog v-model="showNewTicketDialog" @ticket-created="() => {showNewTicketDialog = false}"/>
	</div>
</template>
<script>
import { Dropdown } from 'frappe-ui'
import { inject, ref } from 'vue'
import NewTicketDialog from '@/components/desk/tickets/NewTicketDialog.vue'
import FilterBox from '@/components/desk/global/FilterBox.vue'
import TicketList from '@/components/desk/tickets/TicketList.vue'
import ListManager from '@/components/global/ListManager.vue'
import CustomIcons from '@/components/desk/global/CustomIcons.vue'

export default {
	name: 'Tickets',
	components: {
		NewTicketDialog,
		Dropdown,
		FilterBox,
		ListManager,
		TicketList,
		CustomIcons
	},
	data() {
		return {
			initialFilters: [],
			initialPage: 1
		}
	},
	setup() {
		const user = inject('user')
		const showNewTicketDialog = ref(false)

		const listManagerInitialised = ref(false)

		const filters = ref([])
		const toggleFilters = ref(false)

		const ticketTypes = inject('ticketTypes')
		const ticketPriorities = inject('ticketPriorities')
		const ticketStatuses = inject('ticketStatuses')
		const agents = inject('agents')
		const contacts = inject('contacts')

		return {
			user, 
			showNewTicketDialog, 
			listManagerInitialised,
			filters,
			toggleFilters,
			ticketTypes,
			ticketPriorities,
			ticketStatuses,
			agents,
			contacts
		}
	},
	mounted() {
		if (this.$route.query) {
			for (const [key, value] of Object.entries(this.$route.query)) {
				if (['ticket_type', 'contact', 'status', 'priority', '_assign'].includes(key)) {
					const filter = {}
					filter[key] = value
					this.filters.push(filter)
				}
			} 
		}
		this.applyFiltersToList()
	},
	watch: {
		filters(newValue) {
			let query = {}
			
			if (this.$route.query.menu_filter) {
				query['menu_filter'] = this.$route.query.menu_filter
			}

			newValue.forEach(filter => {
				for (const [key, value] of Object.entries(filter)) {
					if (['ticket_type', 'contact', 'status', 'priority', '_assign'].includes(key)) {
						if (key == '_assign') {
							query.menu_filter = 'all'
						}
						query[key] = value
					}
				}
			})
			this.$router.push({path: this.$route.path, query})
		},
		$route() {
			if(this.$route.name === 'DeskTickets') {
				this.applyFiltersToList()
			}
		}
	},
	methods: {
		applyFiltersToList() {
			const finalFilters = {}
			const menuFilter = this.$route.query.menu_filter
			if (this.user.agent) {
				const sideBarFilters = {
					myOpenTickets: 'my-open-tickets',
					myRepliedTickets: 'my-replied-tickets',
					myResolecedTickets: 'my-resolved-tickets',
					myClosedTickets: 'my-closed-tickets'
				}
				if (Object.values(sideBarFilters).includes(menuFilter)) {
					finalFilters['_assign'] = ['like', `%${this.user.agent.name}%`]
				}
				switch(menuFilter) {
					case sideBarFilters['myOpenTickets']:
						finalFilters['status'] = ['like', '%Open%']
						break;
					case sideBarFilters['myRepliedTickets']:
						finalFilters['status'] = ['like', '%Replied%']
						break;
					case sideBarFilters['myResolecedTickets']:
						finalFilters['status'] = ['like', '%Resolved%']
						break;
					case sideBarFilters['myClosedTickets']:
						finalFilters['status'] = ['like', '%Closed%']
						break;
				}
			}
			this.filters.forEach(filter => {
				for (const [key, value] of Object.entries(filter)) {
					finalFilters[key] = (key === '_assign') ?  ['like', `%${value}%`] : ['=', value]
				}
			})
			if (this.listManagerInitialised) {
				if (JSON.stringify(finalFilters) != JSON.stringify(this.$refs.ticketList.manager.options.filters)) {
					this.$refs.ticketList.manager.update({filters: finalFilters})
				}
			} else {
				this.initialFilters = finalFilters
				this.initialPage = parseInt(this.$route.query.page ? this.$route.query.page : 1)
				this.listManagerInitialised = true
			}
		},
		filterBoxOptions() {
			return [
				{label: "Type", name: "ticket_type", items: this.ticketTypes.map((item) => item.name)},
				{label: "Contact", name: "contact", items: this.contacts.map((item) => item.name)},
				{label: "Status", name: "status", items: this.ticketStatuses},
				{label: "Assignee", name: "_assign", items: this.agents.map((item) => item.name)},
				{label: "Priority", name: "priority", items: this.ticketPriorities.map((item) => item.name)},
				// TODO: {label: "Created On", name: "creation", type: 'calander'}
			]
		},
		markSelectedTicketsAsClosed() {
			this.$resources.bulkAssignTicketStatus.submit({
				ticket_ids: Object.keys(this.$refs.ticketList.selectedItems),
				status: 'Closed'
			})
		},
		agentsAsDropdownOptions() {
			let agentItems = [];
			if (this.agents) {
				this.agents.forEach(agent => {
					agentItems.push({
						label: agent.agent_name,
						handler: () => {
							this.$resources.bulkAssignTicketToAgent.submit({
								ticket_ids: Object.keys(this.$refs.ticketList.selectedItems),
								agent_id: agent.name
							})
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
									this.$resources.bulkAssignTicketToAgent.submit({
										ticket_ids: Object.keys(this.$refs.ticketList.selectedItems),
										agent_id: this.user.agent.name
									})
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
	},
	resources: {
		bulkAssignTicketStatus() {
			return {
				method: 'frappedesk.api.ticket.bulk_assign_ticket_status',
				onSuccess: () => {
					this.$refs.ticketList.selectedItems = []
					this.$refs.ticketList.manager.reload()

					this.$toast({
						title: 'Tickets marked as closed.',
						customIcon: 'circle-check',
						appearance: 'success',
					})

					this.$event.emit('update_ticket_list')

				},
				onError: () => {
					this.$toast({
						title: 'Unable to mark tickets as closed.',
						customIcon: 'circle-fail',
						appearance: 'danger',
					})
				}
			}
		},
		bulkAssignTicketToAgent() {
			return {
				method: 'frappedesk.api.ticket.bulk_assign_ticket_to_agent',
				onSuccess: () => {
					this.$refs.ticketList.selectedItems = []
					this.$refs.ticketList.manager.reload()

					this.$toast({
						title: 'Tickets assigned to agent.',
						customIcon: 'circle-check',
						appearance: 'success',
					})

					this.$event.emit('update_ticket_list')
				},
				onError: () => {
					this.$toast({
						title: 'Unable to assign tickets to agent.',
						customIcon: 'circle-fail',
						appearance: 'danger',
					})
				}
			}
		},
	}
}
</script>
