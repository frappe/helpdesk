<template>
	<div>
		<ListManager
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
			}"
		>
			<template #body="{ manager }">
				<div>
					<div class="flow-root py-4 px-[16px]">
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
						:style="{ height: viewportWidth > 768 ? 'calc(100vh - 6.4rem)' : null }"
					>
						<div v-if="manager.loading">
							<div v-for="n in 3" :key="n">
								<TicketListItemSkeleton />
							</div>
						</div>
						<div v-else v-for="ticket in manager.list" :key="ticket.name">
							<TicketListItem :ticket="ticket" @toggle-select="manager.select(ticket)" :selected="manager.itemSelected(ticket)" />
						</div>
						<div v-if="!manager.loading" class="flex justify-center">
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
import { Input, Dropdown, FeatherIcon, Dialog } from 'frappe-ui'
import NewTicketDialog from '@/components/desk/tickets/NewTicketDialog.vue'
import CustomIcons from '@/components/desk/global/CustomIcons.vue'
import FilterBox from '@/components/desk/global/FilterBox.vue'
import { inject, ref } from 'vue'
import TicketListItem from '@/components/desk/tickets/TicketListItem.vue'
import TicketListItemSkeleton from '@/components/desk/tickets/TicketListItemSkeleton.vue'
import ListManager from '@/components/global/ListManager.vue'
import LoadingText from 'frappe-ui/src/components/LoadingText.vue'

export default {
	name: 'Tickets',
	components: {
    Input,
    Dialog,
    NewTicketDialog,
    CustomIcons,
    Dropdown,
    FeatherIcon,
    FilterBox,
    ListManager,
    TicketListItem,
	TicketListItemSkeleton,
    LoadingText
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

		const viewportWidth = inject('viewportWidth')

		const showSelectAllCheckbox = ref(false)

		return {
			showSelectAllCheckbox,
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
			viewportWidth
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
			let query = this.$route.query.menu_filter ? {menu_filter: this.$route.query.menu_filter} : {}
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
			this.applyFiltersToList()
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
			this.$refs.ticketList.manager.update({filters: finalFilters})
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
				},
				onFailure: () => {
					// TODO:
				}
			}
		},
		bulkAssignTicketToAgent() {
			return {
				method: 'frappedesk.api.ticket.bulk_assign_ticket_to_agent',
				onSuccess: () => {
					this.$refs.ticketList.selectedItems = []
					this.$refs.ticketList.manager.reload()
				},
				onFailure: () => {
					// TODO:
				}
			}
		},
	}
}
</script>
