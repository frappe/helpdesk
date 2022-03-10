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
								@click="ticketTemplateOptions().length > 1 ? toggleTemplates : openDefaultTicketTemplate()"
								icon-left="plus" 
								appearance="primary"
							>
								Create New
							</Button>
						</div>
					</template>
				</Dropdown>
			</div>
			<TicketList />
		</div>
	</div>
</template>

<script>
import { inject } from 'vue'
import { Badge, Dropdown } from 'frappe-ui'
import TicketList from '@/components/portal/tickets/TicketList.vue'

export default {
	name: "Tickets",
	components: {
		Badge,
		Dropdown,
		TicketList
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
		ticketTemplateOptions() {
			let templateItems = [];
			if (this.ticketTemplates) {
				this.ticketTemplates.forEach(template => {
					templateItems.push({
						label: template.name,
						handler: () => {
							this.$router.push({
								name: 'TemplatedNewTicket',
								params: {
									templateId: template.template_route
								}
							})
						},
					});
				});
				return templateItems;
			} else {
				return null;
			}
		},
		openDefaultTicketTemplate() {
			this.$router.push({
				name: 'DefaultNewTicket'
			})
		}
	}
}
</script>