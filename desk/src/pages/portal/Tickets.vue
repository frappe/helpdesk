<template>
	<div class="my-20">
		<div class="mx-auto max-w-4xl">
			<div class="flex justify-between items-center mb-2">
				<div class="mb-2">
					<p class="text-4xl font-semibold">Your Tickets</p>
				</div>
				<Dropdown
					placement="right"
					:options="ticketTemplateOptions()"
					:dropdown-width-full="true"
				>
					<template v-slot="{ toggleTemplates }">
						<div>
							<Button 
								@click="ticketTemplates ? toggleTemplates : () => {}" 
								icon-left="plus" 
								appearance="primary"
							>
								Create New
							</Button>
						</div>
					</template>
				</Dropdown>
			</div>
			<div class="pt-4 px-4 pb-2 bg-white border rounded-lg shadow">
				<div v-for="(ticket, index) in tickets" :key="ticket.name" class="space-y-4">
					<router-link :to="`/support/tickets/${ticket.name}`">
						<div class="px-2 pt-2 hover:bg-slate-50 rounded-lg items-center cursor-pointer mb-2">
							<div class="flex justify-between">
								<div class="font-semibold">{{ ticket.subject }}</div>
								<Badge :color="getStatusBadgeColor(ticket.status)">{{ getStatus(ticket.status) }}</Badge>
							</div>
							<div class="pb-2">
								<div class="text-slate-500">{{ `${$dayjs(ticket.creation).fromNow()} ago` }}</div>
							</div>
							<hr v-if="index != tickets.length - 1"/>
						</div>
					</router-link>
				</div>
			</div>
		</div>
	</div>
</template>

<script>
import { inject } from 'vue'
import { Badge, Dropdown } from 'frappe-ui'

export default {
	name: "Tickets",
	components: {
		Badge,
		Dropdown
	},
	setup() {
		const tickets = inject('tickets')
		const ticketTemplates = inject('ticketTemplates')
		const ticketController = inject('ticketController')

		return { tickets, ticketTemplates, ticketController }
	},
	computed: {
		tickets() {
			return this.tickets || null
		}
	},
	methods: {
		getStatus(status) {
			switch(status) {
				case 'Replied':
					return 'Waiting For Reply'
				case 'Resolved':
					return 'Closed'
				default:
					return status
			}
		},
		getStatusBadgeColor(status) {
			switch(status) {
				case 'Replied':
					return 'yellow'
				case 'Resolved':
					return 'green'
				case 'On Hold':
					return 'blue'
				case 'Closed':
					return 'green'
				case 'Open':
					return 'red'
			}
		},
		ticketTemplateOptions() {
			let templateItems = [];
			if (this.ticketTemplates) {
				this.ticketTemplates.forEach(type => {
					templateItems.push({
						label: type.name,
						handler: () => {
							// TODO: redirect to new ticket page 
						},
					});
				});
				return templateItems;
			} else {
				return null;
			}
		}
	}
}
</script>