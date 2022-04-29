<template>
	<div class="mb-20">
		<div class="mx-auto max-w-4xl">
			<div class="flex justify-between items-center mb-2">
				<div class="mb-2">
					<Dropdown :options="getTicketFilterOptions()">
						<template v-slot="{ toggleTicketFilters }" @click="toggleTicketFilters">
							<div class="flex space-x-2 items-center cursor-pointer">
								<p class="text-4xl font-semibold">{{ this.ticketFilter }}</p>
								<FeatherIcon name="chevron-down" class="w-5 h-5" />
							</div>
						</template>
					</Dropdown>
				</div>
				<div class="space-x-3 items-center flex">
					<Dropdown
						placement="right"
						:options="ticketTemplateOptions().length > 1 ? ticketTemplateOptions() : []"
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
			<TicketList :filter="ticketFilter" />
		</div>
	</div>
</template>

<script>
import { inject, ref } from 'vue'
import { Badge, Dropdown, FeatherIcon } from 'frappe-ui'
import TicketList from '@/components/portal/tickets/TicketList.vue'
import CustomIcons from '@/components/desk/global/CustomIcons.vue'

export default {
	name: "Tickets",
	components: {
		Badge,
		Dropdown,
		TicketList,
		CustomIcons,
		FeatherIcon
	},
	setup() {
		const tickets = inject('tickets')
		const ticketTemplates = inject('ticketTemplates')
		const ticketFilter = ref('All Tickets')

		return { tickets, ticketTemplates, ticketFilter }
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
		},
		getTicketFilterOptions() {
			let items = [];
			["All Tickets", "Open Tickets", "Closed Tickets"].forEach(item => {
				items.push({
				label: item,
					handler: () => {
						this.ticketFilter = item
					},
				});
			});
			return items;
		},
	}
}
</script>