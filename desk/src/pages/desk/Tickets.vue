<template>
	<div>

		<div class="flow-root pt-4 pb-6 pr-[26.14px] pl-[18px]">
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
					>
						<template v-slot="{ toggleAssignees }">
							<div class="flex flex-col">
								<Button @click="toggleAssignees" class="cursor-pointer">
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
						<FilterBox class="mt-6" v-if="toggleFilters" @close="() => { toggleFilters = false }" :options="getFilterBoxOptions()" v-model="filters"/>
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
		<ListManager
			class="pl-[18px] pr-[24px]"
			ref="ticketList"
			:options="ticketListManagerOptions"
		>
			<template #body="{ manager }">
				<div>
					<div
						@pointerenter="() => { showSelectAllCheckbox = true}"
						@pointerleave="() => { showSelectAllCheckbox = false}"
						class="bg-[#F7F7F7] group flex items-center text-base font-medium text-gray-500 py-[10px] pl-[11px] pr-[49.80px] rounded-[6px] select-none"
					>
						<div class="w-[37px] h-[14px]">
							<Input 
								type="checkbox" 
								@click="manager.selectAll()" 
								:checked="manager.allItemsSelected" 
								class="cursor-pointer mr-1 hover:visible" 
								:class="manager.allItemsSelected || showSelectAllCheckbox ? 'visible' : 'invisible'" 
							/>
						</div>
						<div 
							class="sm:w-1/12 flex flex-row items-center space-x-[7px] cursor-pointer"
							@click="manager.toggleOrderBy('name')"
						>
							<span>#</span>
							<div class="w-[10px]">
								<CustomIcons 
									v-if="manager.options.order_by.split(' ')[0] === 'name'"
									:name="manager.options.order_by.split(' ')[1] === 'desc' ? 'chevron-down' : 'chevron-up'"
									class="h-[6px] fill-gray-400 stroke-transparent" 
								/>
							</div>
						</div>
						<div 
							class="sm:w-8/12 flex flex-row items-center space-x-[6px] cursor-pointer"
							@click="manager.toggleOrderBy('subject')"
						>
							<span>Subject</span>
							<div class="w-[10px]">
								<CustomIcons 
									v-if="manager.options.order_by.split(' ')[0] === 'subject'"
									:name="manager.options.order_by.split(' ')[1] === 'desc' ? 'chevron-down' : 'chevron-up'"
									class="h-[6px] fill-gray-400 stroke-transparent" 
								/>
							</div>
						</div>
						<div 
							class="sm:w-3/12 flex flex-row items-center space-x-[6px] cursor-pointer"
							@click="manager.toggleOrderBy('status')"
						>
							<span>Status</span>
							<div class="w-[10px]">
								<CustomIcons 
									v-if="manager.options.order_by.split(' ')[0] === 'status'"
									:name="manager.options.order_by.split(' ')[1] === 'desc' ? 'chevron-down' : 'chevron-up'"
									class="h-[6px] fill-gray-400 stroke-transparent" 
								/>
							</div>
						</div>
						<div 
							class="sm:w-3/12 flex flex-row items-center space-x-[6px] cursor-pointer"
							@click="manager.toggleOrderBy('contact')"
						>
							<span>Created By</span>
							<div class="w-[10px]">
								<CustomIcons 
									v-if="manager.options.order_by.split(' ')[0] === 'contact'"
									:name="manager.options.order_by.split(' ')[1] === 'desc' ? 'chevron-down' : 'chevron-up'"
									class="h-[6px] fill-gray-400 stroke-transparent" 
								/>
							</div>
						</div>
						<div 
							class="sm:w-2/12 flex flex-row items-center space-x-[6px] cursor-pointer"
							@click="manager.toggleOrderBy('resolution_by')"
						>
							<span>Due In</span>
							<div class="w-[10px]">
								<CustomIcons 
									v-if="manager.options.order_by.split(' ')[0] === 'resolution_by'"
									:name="manager.options.order_by.split(' ')[1] === 'desc' ? 'chevron-down' : 'chevron-up'"
									class="h-[6px] fill-gray-400 stroke-transparent" 
								/>
							</div>
						</div>
						<div
							class="sm:w-1/12 flex flex-row items-center space-x-[6px] cursor-pointer"
							@click="manager.toggleOrderBy('modified')"
						>
							<span>Modified</span>
							<div class="w-[10px]">
								<CustomIcons 
									v-if="manager.options.order_by.split(' ')[0] === 'modified'"
									:name="manager.options.order_by.split(' ')[1] === 'desc' ? 'chevron-down' : 'chevron-up'"
									class="h-[6px] fill-gray-400 stroke-transparent" 
								/>
							</div>
						</div>
					</div>
					<div 
						id="rows" 
						class="flex flex-col space-y-2 overflow-scroll"
						:style="{ height: viewportWidth > 768 ? 'calc(100vh - 7rem)' : null }"
					>
						<div v-for="ticket in manager.list" :key="ticket.name">
							<TicketListItem :ticket="ticket" @toggle-select="manager.select(ticket)" :selected="manager.itemSelected(ticket)" />
						</div>
						<div class="flex justify-center">
							<div class="flex flex-row space-x-2">
								<Button appearance="minimal" icon-left="chevron-left" @click="manager.previousPage()">Previous</Button>
								<Button appearance="primary"> {{ manager.currPage }} </Button>
								<Button appearance="minimal" @click="manager.getPage(manager.currPage + 1)"> {{ manager.currPage + 1 }} </Button>
								<Button appearance="minimal" @click="manager.getPage(manager.currPage + 2)"> {{ manager.currPage + 2 }}</Button>
								<Button appearance="minimal" icon-right="chevron-right" @click="manager.nextPage()">Next</Button>
							</div>
						</div>
					</div>
				</div>
			</template>
		</ListManager>
		<NewTicketDialog v-model="showNewTicketDialog" @ticket-created="() => {showNewTicketDialog = false}"/>
	</div>
</template>
<script>
import { Input, Dropdown, FeatherIcon, ListManager, Dialog } from 'frappe-ui'
import TicketList from '@/components/desk/tickets/TicketList.vue'
import NewTicketDialog from '@/components/desk/tickets/NewTicketDialog.vue'
import CustomIcons from '@/components/desk/global/CustomIcons.vue'
import FilterBox from '@/components/desk/global/FilterBox.vue'
import { inject, ref, provide } from 'vue'
import TicketListItem from '@/components/desk/tickets/TicketListItem.vue'

export default {
	name: 'Tickets',
	components: {
		TicketList,
		Input,
		Dialog,
		NewTicketDialog,
		CustomIcons,
		Dropdown,
		FeatherIcon,
		FilterBox,
		ListManager,
		TicketListItem
	},
	setup() {
		const user = inject('user')
		const tickets = inject('tickets')
		const showNewTicketDialog = ref(false)

		const filters = ref([])
		const toggleFilters = ref(false)

		const ticketTypes = inject('ticketTypes')
		const ticketPriorities = inject('ticketPriorities')
		const ticketStatuses = inject('ticketStatuses')
		const agents = inject('agents')
		const contacts = inject('contacts')

		const selectedTickets = ref([])
		const resetSelections = ref(false)
		provide('resetSelections', resetSelections)

		const ticketController = inject('ticketController')
		const updateSidebarFilter = inject('updateSidebarFilter')
		const viewportWidth = inject('viewportWidth')

		const ticketListManagerOptions = ref({
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
		})

		const showSelectAllCheckbox = ref(false)

		return {
			showSelectAllCheckbox,
			ticketListManagerOptions,
			user, 
			tickets, 
			showNewTicketDialog, 
			filters, 
			toggleFilters,
			ticketTypes,
			ticketPriorities,
			ticketStatuses,
			agents,
			contacts,
			selectedTickets,
			ticketController,
			resetSelections,
			updateSidebarFilter,
			viewportWidth
		}
	},
	mounted() {
		if (this.$route.query) {
			for (const [key, value] of Object.entries(this.$route.query)) {
				if (['ticket_type', 'raised_by', 'status', 'priority', 'assignee'].includes(key)) {
					const filter = {}
					filter[key] = value
					this.filters.push(filter)
				}
			} 
		}

		// this.$refs.ticketList.manager.options.handle_row_click = (rowData) => {
		// 	console.log(`${rowData.name} clicked !!!`)
		// 	this.$router.push({path: `/frappedesk/tickets/${rowData.name}`})
		// }
	},
	watch: {
		filters(newValue) {
			let query = this.$route.query.menu_filter ? {menu_filter: this.$route.query.menu_filter} : {}
			newValue.forEach(filter => {
				for (const [key, value] of Object.entries(filter)) {
					if (['ticket_type', 'raised_by', 'status', 'priority', 'assignee'].includes(key)) {
						if (key == 'assignee') {
							query.menu_filter = 'all'
						}
						query[key] = value
					}
				}
			})
			this.$router.push({path: this.$route.path, query}).then(() => this.updateSidebarFilter())
		}
	},
	computed: {
		showTicketBluckUpdatePanel() {
			return this.selectedTickets.length > 0
		}
	},
	methods: {
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
				this.ticketController.bulkSet(this.selectedTickets, 'status', 'Closed').then(() => {
					this.resetSelections = true
				})
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
								this.ticketController.bulkSet(this.selectedTickets, 'agent', agent.name).then(() => {
									this.resetSelections = true
								})
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
										this.ticketController.bulkSet(this.selectedTickets, 'agent').then(() => {
											this.resetSelections = true
										})
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
