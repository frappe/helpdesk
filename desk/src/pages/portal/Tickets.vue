<template>
	<div class="mb-20">
		<div class="mx-auto max-w-4xl">
			<div class="flex justify-between items-center mb-2">
				<div class="mb-2">
					<p class="text-4xl font-semibold">Your Tickets</p>
				</div>
				<div class="space-x-3 items-center flex">
					<Button type="white">
						<div class="flex items-center space-x-2">
							<CustomIcons height="18" width="18" name="sort-ascending" />
							<div>Sort by created</div>
						</div>
					</Button>
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
			</div>
			<TicketList />
		</div>
	</div>
</template>

<script>
import { inject } from 'vue'
import { Badge, Dropdown } from 'frappe-ui'
import TicketList from '@/components/portal/tickets/TicketList.vue'
import CustomIcons from '@/components/desk/global/CustomIcons.vue'

export default {
	name: "Tickets",
	components: {
		Badge,
		Dropdown,
		TicketList,
		CustomIcons
	},
	setup() {
		const tickets = inject('tickets')
		const ticketTemplates = inject('ticketTemplates')

		return { tickets, ticketTemplates }
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