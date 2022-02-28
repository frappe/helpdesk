<template>
	<div class="my-20">
        <div class="mx-auto max-w-2xl">
            <div class="flex justify-between items-center mb-2">
                <div class="mb-2">
                    <p class="text-4xl font-semibold">Your Tickets</p>
                </div>
                <Button icon-left="plus" appearance="primary">Create New</Button>
            </div>
            <div class="pt-4 px-4 pb-2 bg-white border rounded-lg shadow">
                <div v-for="(ticket, index) in tickets" :key="ticket.name" class="space-y-4">
                    <div class="px-2 pt-2 hover:bg-slate-50 rounded-lg items-center cursor-pointer mb-2">
                        <div class="flex justify-between">
                            <div class="font-semibold">{{ ticket.subject }}</div>
                            <Badge color="green">{{ ticket.status }}</Badge>
                        </div>
                        <div class="pb-2">
                            <div class="text-slate-500">{{ `${$dayjs(ticket.creation).fromNow()} ago` }}</div>
                        </div>
                        <hr v-if="index != tickets.length - 1"/>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<script>
import { inject } from 'vue'
import { Badge } from 'frappe-ui'

export default {
	name: "Tickets",
    components: {
        Badge
    },
    setup() {
        const tickets = inject('tickets')
        const ticketController = inject('ticketController')

        return { tickets, ticketController }
    },
    computed: {
        tickets() {
            return this.tickets || null
        }
    }
}
</script>