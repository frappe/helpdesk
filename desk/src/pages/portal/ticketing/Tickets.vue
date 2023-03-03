<template>
	<div class="mb-20 mt-5">
		<div class="mx-auto max-w-4xl">
			<div class="mb-2 flex items-center justify-between">
				<div class="mb-2">
					<Dropdown :options="getTicketFilterOptions()">
						<template
							#default="{ toggleTicketFilters }"
							@click="toggleTicketFilters"
						>
							<div class="flex cursor-pointer items-center space-x-2">
								<p class="text-[18px] font-semibold">
									{{ ticketFilter }}
								</p>
								<FeatherIcon name="chevron-down" class="h-5 w-5" />
							</div>
						</template>
					</Dropdown>
				</div>
				<div class="flex items-center space-x-3">
					<Dropdown
						placement="right"
						:options="
							ticketTemplateOptions().length > 1 ? ticketTemplateOptions() : []
						"
						:dropdown-width-full="true"
					>
						<template #default="{ toggleTemplates }">
							<div>
								<Button
									icon-left="plus"
									appearance="primary"
									@click="
										ticketTemplateOptions().length > 1
											? toggleTemplates
											: openDefaultTicketTemplate()
									"
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
import { inject, ref } from "vue";
import { Badge, Dropdown, FeatherIcon } from "frappe-ui";
import TicketList from "@/components/portal/tickets/TicketList.vue";
import CustomIcons from "@/components/desk/global/CustomIcons.vue";

export default {
	name: "Tickets",
	components: {
		Badge,
		Dropdown,
		TicketList,
		CustomIcons,
		FeatherIcon,
	},
	setup() {
		const tickets = inject("tickets");
		const ticketTemplates = inject("ticketTemplates");
		const ticketFilter = ref("All Tickets");

		return { tickets, ticketTemplates, ticketFilter };
	},
	computed: {
		tickets() {
			return this.tickets || null;
		},
	},
	methods: {
		ticketTemplateOptions() {
			if (!this.ticketTemplates) return;

			return this.ticketTemplates.map((template) => ({
				label: template.name,
				handler: () => {
					this.$router.push({
						name: "TemplatedNewTicket",
						params: {
							templateId: template.template_route,
						},
					});
				},
			}));
		},
		openDefaultTicketTemplate() {
			this.$router.push({
				name: "DefaultNewTicket",
			});
		},
		getTicketFilterOptions() {
			const opts = ["All Tickets", "Open Tickets", "Closed Tickets"];

			return opts.map((item) => ({
				label: item,
				handler: () => {
					this.ticketFilter = item;
				},
			}));
		},
	},
};
</script>
