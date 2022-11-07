<template>
	<div class="flex flex-col h-full p-4">
		<ListManager
			ref="ticketList"
			:options="{
				cache: ['Ticket', 'Desk'],
				doctype: 'Ticket',
				fields: [
					'priority',
					'name',
					'subject',
					'ticket_type',
					'status',
					'contact',
					'response_by',
					'resolution_by',
					'agreement_status',
					'creation',
					'modified',
					'_assign',
					'_seen',
				],
				limit: 20,
				order_by: 'modified desc',
				filters: initialFilters,
			}"
		>
			<template #body="{ manager }">
				<ListViewer
					:manager="manager"
					:options="{
						base: '24',
						showFilterBox: false,
						fields: {
							name: {
								label: '#',
								width: '1',
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
								width: '3',
							},
							priority: {
								label: 'Priority',
								width: '2',
							},
							contact: {
								label: 'Created By',
								width: '3',
							},
							creation: {
								label: 'Created',
								width: '2',
							},
							modified: {
								label: 'Modified',
								width: '2',
							},
							_assign: {
								label: ' ',
								width: '1',
								align: 'right',
							},
						},
					}"
					class="text-base"
				>
					<!-- Field Templates -->
					<template #field-name="{ value }">
						<div class="text-xs text-gray-500">
							{{ value }}
						</div>
					</template>
					<template #field-status="{ value }">
						<div class="flex flex-row items-center space-x-1">
							<FeatherIcon
								v-if="value != 'Open'"
								:name="
									{
										Closed: 'lock',
										Resolved: 'check',
										Replied: 'corner-up-left',
									}[value]
								"
								class="stroke-gray-600 w-[12px] h-[12px] mx-[2px]"
							/>
							<CustomIcons
								v-else
								name="comment"
								class="w-[16px] h-[16px] stroke-green-600"
							/>
							<div
								class="text-base font-normal"
								:class="
									value == 'Open'
										? 'text-green-600'
										: 'text-gray-600'
								"
							>
								{{ value }}
							</div>
						</div>
					</template>
					<template #field-priority="{ value }">
						<div class="flex flex-row items-center space-x-1">
							<div
								class="text-sm font-semibold px-2 border rounded-lg"
								:class="{
									'text-green-500': value == 'Low',
									'text-yellow-500': value == 'Medium',
									'text-orange-500': value == 'High',
									'text-red-500': value == 'Urgent',
									'bg-green-100': value == 'Low',
									'bg-yellow-100': value == 'Medium',
									'bg-orange-100': value == 'High',
									'bg-red-100': value == 'Urgent',
									'border-green-500': value == 'Low',
									'border-yellow-500': value == 'Medium',
									'border-orange-500': value == 'High',
									'border-red-500': value == 'Urgent',
								}"
							>
								{{ value.toLowerCase() }}
							</div>
						</div>
					</template>
					<template #field-contact="{ value }">
						<div class="text-gray-500">
							{{ value }}
						</div>
					</template>
					<template #field-creation="{ value }">
						<div class="text-gray-500">
							{{
								$dayjs.longFormating(
									$dayjs(value).fromNow(),
									false
								)
							}}
						</div>
					</template>
					<template #field-modified="{ value }">
						<div class="text-gray-500">
							{{
								$dayjs.longFormating(
									$dayjs(value).fromNow(),
									false
								)
							}}
						</div>
					</template>
					<template #field-_assign="{ value }">
						<AgentAvatar :agent="JSON.parse(value)[0]" />
					</template>

					<!-- Other Templates -->
					<template #bulk-actions="{ selectedItems }">
						<div class="flex flex-row space-x-2">
							<Dropdown
								placement="right"
								:options="agentsAsDropdownOptions()"
							>
								<template v-slot="{ toggleDropdown }">
									<Button
										:loading="
											$resources.bulkAssignTicketToAgent
												.loading
										"
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
												ticket_ids:
													Object.keys(selectedItems),
												status: 'Closed',
											})
											.then(() => {
												manager.unselect()
												manager.reload()
											})
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
	</div>
</template>
<script>
import ListManager from "@/components/global/ListManager.vue"
import ListViewer from "@/components/global/ListViewer.vue"
import AgentAvatar from "@/components/global/AgentAvatar.vue"
import CustomIcons from "@/components/desk/global/CustomIcons.vue"
import { FeatherIcon, Dropdown } from "frappe-ui"

export default {
	name: "Tickets",
	components: {
		ListManager,
		ListViewer,
		AgentAvatar,
		CustomIcons,
		FeatherIcon,
		Dropdown,
	},
	inject: ["agents", "user"],
	mounted() {
		if (this.$route.query) {
			for (const [key, value] of Object.entries(this.$route.query)) {
				if (
					[
						"ticket_type",
						"contact",
						"status",
						"priority",
						"_assign",
					].includes(key)
				) {
					const filter = {}
					filter[key] = value
					this.filters.push(filter)
				}
			}
		}
		// TODO: this.applyFiltersToList()
	},
	methods: {
		agentsAsDropdownOptions() {
			let agentItems = []
			if (this.agents) {
				this.agents.forEach((agent) => {
					agentItems.push({
						label: agent.agent_name,
						handler: () => {
							this.$resources.bulkAssignTicketToAgent.submit({
								ticket_ids: Object.keys(
									this.$refs.ticketList.selectedItems
								),
								agent_id: agent.name,
							})
						},
					})
				})
				let options = []
				if (this.user.agent) {
					options.push({
						group: "Myself",
						hideLabel: true,
						items: [
							{
								label: "Assign to me",
								handler: () => {
									this.$resources.bulkAssignTicketToAgent.submit(
										{
											ticket_ids: Object.keys(
												this.$refs.ticketList
													.selectedItems
											),
											agent_id: this.user.agent.name,
										}
									)
								},
							},
						],
					})
				}
				options.push({
					group: "All Agents",
					hideLabel: true,
					items: agentItems,
				})
				return options
			} else {
				return null
			}
		},
	},
	resources: {
		bulkAssignTicketStatus() {
			return {
				method: "frappedesk.api.ticket.bulk_assign_ticket_status",
				onSuccess: (res) => {
					//res: {docs: Ticket Docs, status: NewStatus}
					this.$refs.ticketList.selectedItems = []
					this.$refs.ticketList.manager.reload()

					this.$toast({
						title: `Tickets marked as ${res.status}.`,
						customIcon: "circle-check",
						appearance: "success",
					})

					this.$event.emit("update_ticket_list")
				},
				onError: () => {
					this.$toast({
						title: "Unable to mark tickets as closed.",
						customIcon: "circle-fail",
						appearance: "danger",
					})
				},
			}
		},
		bulkAssignTicketToAgent() {
			return {
				method: "frappedesk.api.ticket.bulk_assign_ticket_to_agent",
				onSuccess: () => {
					this.$refs.ticketList.selectedItems = []
					this.$refs.ticketList.manager.reload()

					this.$toast({
						title: "Tickets assigned to agent.",
						customIcon: "circle-check",
						appearance: "success",
					})

					this.$event.emit("update_ticket_list")
				},
				onError: () => {
					this.$toast({
						title: "Unable to assign tickets to agent.",
						customIcon: "circle-fail",
						appearance: "danger",
					})
				},
			}
		},
	},
}
</script>
