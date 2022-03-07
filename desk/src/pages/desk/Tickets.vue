<template>
	<div>
		<div class="flow-root border-b pt-2 pb-3 pr-8">
			<div class="float-right flex space-x-3">
				<Button type="white">
					<div class="flex items-center space-x-2">
						<CustomIcons height="18" width="18" name="filter" />
						<div>Add filter</div>
					</div>
				</Button>
				<Button type="white">
					<div class="flex items-center space-x-2">
						<CustomIcons height="18" width="18" name="sort-ascending" />
						<div>Last Modified On</div>
					</div>
				</Button>
				<Button icon-left="plus" appearance="primary" @click="() => {showNewTicketDialog = true}">Add Ticket</Button>
			</div>
		</div>
		<div v-if="tickets">
			<TicketList />
		</div>
		<NewTicketDialog v-model="showNewTicketDialog" @ticket-created="() => {showNewTicketDialog = false}"/>
	</div>
</template>
<script>
import { Input } from 'frappe-ui'
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
		CustomIcons
	},
	setup() {
		const tickets = inject('tickets')
		const showNewTicketDialog = ref(false)

		return { tickets, showNewTicketDialog }
	},
	activated() {
		this.$currentPage.set('Tickets')
	}
}

// TODO: transfer the tickets controllers to desk.vue file
</script>
