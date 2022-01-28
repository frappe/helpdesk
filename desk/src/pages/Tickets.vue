<template>
	<div 
        class="flex mx-4 py-4"
        :style="{ height: viewportWidth > 768 ? 'calc(100vh - 1rem)' : null }"
    >
        <div class="sm:w-1/12 bg-slate-100 mr-4">

        </div>
        <div class="sm:w-11/12">
            <div class="mb-4">
                <Button type="primary">Add Ticket</Button>
            </div>
            <div class="w-full">
                <TicketList v-bind:tickets="$resources.allTickets.data"/>
            </div>
        </div>
    </div>
</template>
<script>
import TicketList from './TicketList.vue'

export default {
	name: 'Tickets',
    inject: ['viewportWidth'],
    resources: {
		allTickets: {
		method: 'helpdesk.api.ticket.get_tickets',
		},
	},
	components: {
        TicketList
	},
	mounted() {
		this.$resources.allTickets.fetch()
	}
}
</script>
