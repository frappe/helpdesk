<template>
	<div>
		<div class="flow-root pt-2 pb-5 pr-8 pl-4">
			<div class="float-left">
				<div v-if="ticketFilterDropdownOptions().length > 0">
					<Dropdown
							placement="left"
							:options="ticketFilterDropdownOptions()"
						>
						<template v-slot="{ toggleDropdown }"> 
							<div class="flex items-center cursor-pointer" @click="toggleDropdown">
								<div class="text-2xl">
									{{ this.ticketFilter }}
								</div>
								<FeatherIcon class="ml-2 stroke-slate-600 h-5 w-5" name="chevron-down"/>
							</div>
						</template>
					</Dropdown>
				</div>
				<div v-else class="text-2xl">All Tickets</div>
			</div>
			<div class="float-right flex space-x-3 stroke-blue-600">
				<Button :class="Object.keys(filters).length == 0 ? 'bg-gray-100 text-gray-600' : 'bg-blue-100 text-blue-500 hover:bg-blue-200'">
					<div class="flex items-center space-x-2">
						<CustomIcons height="18" width="18" name="filter" :class="Object.keys(filters).length > 0 ? 'stroke-blue-600' : 'stroke-black'" />
						<div>Add Filters</div>
						<div class="bg-blue-500 text-white px-1.5 rounded" v-if="Object.keys(filters).length > 0">{{ Object.keys(this.filters).length }}</div>
					</div>
				</Button>
				<Button type="white" @click="() => { toggleSort('modified') }">
					<div class="flex items-center space-x-2">
						<CustomIcons height="18" width="18" name="sort-ascending" />
						<div>Last Modified On</div>
					</div>
				</Button>
				<Button icon-left="plus" appearance="primary" @click="() => {showNewTicketDialog = true}">Add Ticket</Button>
			</div>
		</div>
		<div v-if="tickets">
			<TicketList :sortby="sortby" :sortDirection="sortDirection" :filters="filters" />
		</div>
		<NewTicketDialog v-model="showNewTicketDialog" @ticket-created="() => {showNewTicketDialog = false}"/>
	</div>
</template>
<script>
import { Input, Dropdown, FeatherIcon } from 'frappe-ui'
import TicketList from '@/components/desk/tickets/TicketList.vue'
import NewTicketDialog from '@/components/desk/tickets/NewTicketDialog.vue'
import CustomIcons from '@/components/desk/global/CustomIcons.vue'
import { inject, ref } from 'vue'

export default {
	name: 'Tickets',
	components: {
		TicketList,
		Input,
		NewTicketDialog,
		CustomIcons,
		Dropdown,
		FeatherIcon
	},
	setup() {
		const user = inject('user')
		const tickets = inject('tickets')
		const ticketFilter = inject('ticketFilter')
		const showNewTicketDialog = ref(false)

		const filters = ref({})
		const sortby = ref('modified')
		const sortDirection = ref('dessending')

		return { user, tickets, ticketFilter, showNewTicketDialog, filters, sortby, sortDirection }
	},
	activated() {
		this.$currentPage.set('Tickets')
	},
	methods: {
		ticketFilterDropdownOptions() {
			let items = [];
			(this.user.agent ? ["All Tickets", "Assigned to me"] : []).forEach(filter => {
				items.push({
					label: filter,
					handler: () => {
						this.ticketFilter = filter;
						
						if (filter == 'Assigned to me') {
							this.filters.assignee = this.user.agent.name
						} else {
							delete this.filters.assignee
						}
					}
				});
			});
			return items;
		},
		toggleSort(sortby) {
			if (this.sortby != sortby) {
				this.sortDirection = 'assending'
				this.sortby = sortby
			} else {
				this.sortDirection = (this.sortDirection == 'assending' ? 'dessending' : 'assending')
			}
		}
	}
}

// TODO: transfer the tickets controllers to desk.vue file
</script>
