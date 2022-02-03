<template>
	<div class="flex">
		<div class="sm:w-3/12 px-4 space-y-5">
			<div>
				<Card title="Contact details" subtitle="Sub text">
					<div class="text-base">Card content</div>
				</Card>
			</div>
			<div v-if="ticket">
				<Card :title="'Ticket #' + ticket.name" subtitle="Sub text">
					<div class="text-base">Ticket Actions</div>
				</Card>
			</div>
		</div>
		<div 
			v-if="ticket"
			class="sm:w-9/12 px-4"
			:style="{ height: viewportWidth > 768 ? 'calc(100vh - 8rem)' : null }"
		>
			<div class="flex">
				<div class="text-6xl">
					{{ ticket.name }} - {{ ticket.subject }}
				</div>
				<Badge color="green" class="my-2 ml-3">{{ ticket.status }}</Badge>
			</div>
		</div>
	</div>
</template>
<script>
import { Badge } from 'frappe-ui'
import { Card } from 'frappe-ui'

export default {
	name: 'TicketConversation',
	inject: ['viewportWidth'],
	props: ['ticketId'],
	components: {
		Badge,
		Card
	},
	resources: {
		ticket() {
			return {
				method: 'helpdesk.api.ticket.get_ticket',
				params: {
					ticket_id: this.ticketId
				},
				auto: true
			}
		},
	},
	computed: {
		ticket() {
			return this.$resources.ticket.data;
		}
	}
}
</script>