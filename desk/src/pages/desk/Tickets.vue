<template>
	<div class="flex flex-col overflow-y-clip px-4">
		<ListManager
			ref="ticketList"
			:options="{
				cache: ['Ticket', 'Desk'],
				urlQueryFilters: true,
				saveFiltersLocally: true,
				doctype: 'Ticket',
				fields: [
					'_assign',
					'status',
					'priority',
					'subject',
					'ticket_type',
					'agent_group',
					'contact',
					'creation',
					'modified',
					'name',
					'response_by',
					'resolution_by',
					'agreement_status',
					'_seen',
				],
				limit: 20,
				order_by: 'modified desc',
			}"
		>
			<template #body="{ manager }">
				<ListViewer
					:options="{
						base: '24',
						filterBox: true,
						presetFilters: true,
						fields: {
							name: {
								label: '#',
								width: '2',
							},
							subject: {
								label: 'Subject',
								width: '9',
							},
							status: {
								label: 'Status',
								width: '2',
							},
							ticket_type: {
								label: 'Type',
								width: '2',
							},
							priority: {
								label: 'Priority',
								width: '2',
							},
							resolution_by: {
								label: 'Due In',
								width: '2',
							},
							contact: {
								label: 'Created By',
								width: '3',
							},
							modified: {
								label: 'Modified',
								width: '2',
							},
						},
					}"
					class="h-[calc(100vh-5.5rem)] pt-4 text-base"
					@add-item="
						() => {
							showNewTicketDialog = true;
						}
					"
				>
					<!-- Field Templates -->
					<template #field-name="{ value }">
						<div class="text-gray-500">
							{{ value }}
						</div>
					</template>
					<template #field-subject="{ row }">
						<Subject :ticket="row" />
					</template>
					<template #field-status="{ value }">
						<TicketStatus :value="value" />
					</template>
					<template #field-priority="{ value }">
						<TicketPriority :value="value" />
					</template>
					<template #field-ticket_type="{ value }">
						<TicketType :value="value" />
					</template>
					<template #field-contact="{ value }">
						<div class="text-gray-500">
							{{ value }}
						</div>
					</template>
					<template #field-creation="{ value }">
						<Tooltip placement="top" :text="`Created on ${$dayjs(value)}`">
							<div class="text-gray-500">
								{{ $dayjs(value).format("DD MMM") }}
							</div>
						</Tooltip>
					</template>
					<template #field-resolution_by="{ row }">
						<ResolutionBy :ticket="row" />
					</template>
					<template #field-modified="{ row }">
						<div class="flex w-full justify-between">
							<div class="text-gray-500">
								{{
									$dayjs.shortFormating($dayjs(row.modified).fromNow(), false)
								}}
							</div>
							<AgentAvatar
								v-if="row._assign"
								:agent="JSON.parse(row._assign)[0]"
							/>
						</div>
					</template>

					<!-- Other Templates -->
					<template #bulk-actions="{ selectedItems }">
						<div class="flex flex-row space-x-2">
							<Dropdown placement="right" :options="agentsAsDropdownOptions()">
								<template #default="{ toggleDropdown }">
									<Button
										:loading="$resources.bulkAssignTicketToAgent.loading"
										icon-right="chevron-down"
										class="ml-2"
										@click="toggleDropdown"
									>
										Assign to
									</Button>
								</template>
							</Dropdown>
							<!-- <Button @click="() => {}">Add to FAQ</Button> -->
							<Button
								@click="
									() => {
										$resources.bulkAssignTicketStatus
											.submit({
												ticket_ids: Object.keys(selectedItems),
												status: 'Closed',
											})
											.then(() => {
												manager.unselect();
												manager.reload();
											});
									}
								"
							>
								Close Ticket
							</Button>
						</div>
					</template>
				</ListViewer>
			</template>
		</ListManager>
		<NewTicketDialog
			v-model="showNewTicketDialog"
			@close="showNewTicketDialog = false"
			@ticket-created="
				() => {
					showNewTicketDialog = false;
					$refs.ticketList.manager.reload(); // TODO: remove this once the list manager realtime update is fixed
				}
			"
		/>
	</div>
</template>

<script>
import { FeatherIcon, Dropdown, Tooltip } from "frappe-ui";
import ListManager from "@/components/global/ListManager.vue";
import ListViewer from "@/components/global/ListViewer.vue";
import AgentAvatar from "@/components/global/AgentAvatar.vue";
import ResolutionBy from "@/components/global/ticket_list_item/ResolutionBy.vue";
import TicketType from "@/components/global/ticket_list_item/TicketType.vue";
import TicketStatus from "@/components/global/ticket_list_item/TicketStatus.vue";
import TicketPriority from "@/components/global/ticket_list_item/TicketPriority.vue";
import Subject from "@/components/global/ticket_list_item/Subject.vue";
import NewTicketDialog from "@/components/desk/tickets/NewTicketDialog.vue";

export default {
	name: "Tickets",
	components: {
		ListManager,
		ListViewer,
		AgentAvatar,
		NewTicketDialog,
		FeatherIcon,
		Dropdown,
		Tooltip,
		ResolutionBy,
		TicketType,
		TicketStatus,
		TicketPriority,
		Subject,
	},
	inject: ["agents", "user"],
	data() {
		return {
			showNewTicketDialog: false,
		};
	},
	methods: {
		agentsAsDropdownOptions() {
			let agentItems = [];
			if (this.agents) {
				this.agents.forEach((agent) => {
					agentItems.push({
						label: agent.agent_name,
						handler: () => {
							this.$resources.bulkAssignTicketToAgent.submit({
								ticket_ids: Object.keys(
									this.$refs.ticketList.manager.selectedItems
								),
								agent_id: agent.name,
							});
						},
					});
				});
				let options = [];
				if (this.user.agent) {
					options.push({
						group: "Myself",
						hideLabel: true,
						items: [
							{
								label: "Assign to me",
								handler: () => {
									this.$resources.bulkAssignTicketToAgent.submit({
										ticket_ids: Object.keys(
											this.$refs.ticketList.manager.selectedItems
										),
										agent_id: this.user.agent.name,
									});
								},
							},
						],
					});
				}
				options.push({
					group: "All Agents",
					hideLabel: true,
					items: agentItems,
				});
				return options;
			} else {
				return null;
			}
		},
	},
	resources: {
		bulkAssignTicketStatus() {
			return {
				method: "frappedesk.api.ticket.bulk_assign_ticket_status",
				onSuccess: (res) => {
					//res: {docs: Ticket Docs, status: NewStatus}
					this.$refs.ticketList.manager.selectedItems = [];
					this.$refs.ticketList.manager.reload();

					this.$toast({
						title: `Tickets marked as ${res.status}.`,
						customIcon: "circle-check",
						appearance: "success",
					});

					this.$event.emit("update_ticket_list");
				},
				onError: () => {
					this.$toast({
						title: "Unable to mark tickets as closed.",
						customIcon: "circle-fail",
						appearance: "danger",
					});
				},
			};
		},
		bulkAssignTicketToAgent() {
			return {
				method: "frappedesk.api.ticket.bulk_assign_ticket_to_agent",
				onSuccess: () => {
					this.$refs.ticketList.manager.selectedItems = [];
					this.$refs.ticketList.manager.reload();

					this.$toast({
						title: "Tickets assigned to agent.",
						customIcon: "circle-check",
						appearance: "success",
					});

					this.$event.emit("update_ticket_list");
				},
				onError: () => {
					this.$toast({
						title: "Unable to assign tickets to agent.",
						customIcon: "circle-fail",
						appearance: "danger",
					});
				},
			};
		},
	},
};
</script>
