<template>
	<div class="px-3" v-if="ticket">
		<div class="py-4 border-b space-y-3">
			<div class="text-lg font-medium">{{ `Ticket #${ticket.name}` }}</div>
			<div class="text-base space-y-2">
				<div class="flex flex-col space-y-2">
					<div class="text-slate-500">First Response Due</div>
					<div>{{ $dayjs(ticket.response_by).format('ddd, MMM DD, YYYY H:m') }}</div>
				</div>
				<div class="flex flex-col space-y-2">
					<div class="text-slate-500">Resolution Due</div>
					<div>{{ $dayjs(ticket.resolution_by).format('ddd, MMM DD, YYYY H:m') }}</div>
				</div>
			</div>
		</div>
		<div class="py-4 space-y-3" :class="ticket.custom_fields.length > 0 ? 'border-b' : ''">
			<div class="text-base space-y-2">
				<div class="flex flex-col space-y-2">
					<div class="text-slate-500">Assignee</div>
					<CustomDropdown
						v-if="agents"
						:options="agentsAsDropdownOptions()" 
						class="text-base w-56"
					>
						<template v-slot="{ toggleAssignees }" @click="toggleAssignees" class="w-full">
							<div class="flex w-56 py-1 hover:bg-slate-50 space-x-1">
								<div v-if="ticket.assignees.length > 0" class="grow w-52 text-left">{{ ticket.assignees[0].agent_name }}</div>
								<div v-else class="text-base grow w-52 text-left text-gray-400"> assign agent </div>
								<CustomIcons name="select" class="w-4 h-4 float-right" />
							</div>
						</template>
					</CustomDropdown>
				</div>
				<div class="flex flex-col space-y-2">
					<div class="text-slate-500">Status</div>
					<CustomDropdown
						v-if="ticketStatuses"
						:options="statusesAsDropdownOptions()" 
						class="text-base w-56"
					>
						<template v-slot="{ toggleAssignees }" @click="toggleAssignees" class="w-full">
							<div class="w-full">
								<div class="flex w-56 py-1 hover:bg-slate-50 space-x-1">
									<div v-if="ticket.status" class="grow w-52 text-left">{{ ticket.status }}</div>
									<div v-else class="text-base grow w-52 text-left text-gray-400"> set status </div>
								<CustomIcons name="select" class="w-4 h-4 float-right" />
							</div>
							</div>
						</template>
					</CustomDropdown>
				</div>
				<div class="flex flex-col space-y-2">
					<div class="text-slate-500">Team</div>
					<div>Functional</div>
				</div>
				<div class="flex flex-col space-y-2">
					<div class="text-slate-500">Priority</div>
					<CustomDropdown
						v-if="ticketPriorities"
						:options="prioritiesAsDropdownOptions()" 
						class="text-base w-56"
					>
						<template v-slot="{ toggleAssignees }" @click="toggleAssignees" class="w-full">
							<div class="flex w-56 py-1 hover:bg-slate-50 space-x-1">
								<div v-if="ticket.priority" class="grow w-52 text-left">{{ ticket.priority }}</div>
								<div v-else class="text-base grow w-52 text-left text-gray-400"> set priority </div>
								<CustomIcons name="select" class="w-4 h-4 float-right" />
							</div>
						</template>
					</CustomDropdown>
				</div>
				<div class="flex flex-col space-y-2">
					<div class="text-slate-500">Type</div>
					<CustomDropdown
						v-if="ticketTypes"
						:options="typesAsDropdownOptions()" 
						class="text-base w-56"
					>
						<template v-slot="{ toggleAssignees }" @click="toggleAssignees" class="w-full">
							<div class="flex w-56 py-1 hover:bg-slate-50 space-x-1 items-center">
								<div v-if="ticket.ticket_type" class="grow w-52 text-left">{{ ticket.ticket_type }}</div>
								<div v-else class="text-base grow w-52 text-left text-gray-400"> set type </div>
								<CustomIcons name="select" class="w-4 h-4 float-right" />
							</div>
						</template>
					</CustomDropdown>
				</div>
			</div>
		</div>
		<div class="py-4 border-b space-y-3" v-if="ticket.custom_fields.length > 0">
			<div class="text-lg font-medium">{{ `Custom Fields (${ticket.template})` }}</div>
			<div class="text-base space-y-2">
					<div class="flex flex-col space-y-2" v-for="field in ticket.custom_fields" :key="field">
						<div class="text-slate-500">{{ field.fieldname }}</div>
						<div :class="field.route ? 'hover:underline hover:text-blue-500 cursor-pointer' : ''" @click="() => redirectToRoute(field.route)">{{ field.value }}</div>
					</div>
			</div>
		</div>
		<Dialog :options="{title: 'Create New Type'}" v-model="openCreateNewTicketTypeDialog">
			<template #body-content>
				<div class="space-y-4">
					<Input type="text" v-model="newType" placeholder="eg: Bug" />
					<div class="flex float-right space-x-2">
						<Button @click="createAndAssignTicketTypeFromDialog()">Create and Assign</Button>
						<Button @click="createTicketFromDialog()" appearance="primary">Create</Button>
					</div>
				</div>
			</template>
		</Dialog>
	</div>
</template>

<script>
import { FeatherIcon, Dropdown, Input, Dialog } from 'frappe-ui'
import CustomDropdown from '@/components/desk/global/CustomDropdown.vue'
import CustomIcons from '@/components/desk/global/CustomIcons.vue'
import { inject } from '@vue/runtime-core'

export default {
	name: "ActionPanel",
	props: ["ticketId"],
	components: {
		FeatherIcon,
		Dropdown,
		CustomDropdown,
		Input,
		Dialog,
		CustomIcons
	},
	data() {
		return {
			openCreateNewTicketTypeDialog: false,
			newType: "",
		}
	},
	setup() {
		const user = inject('user')
		const tickets = inject('tickets')
		const ticketTypes = inject('ticketTypes')
		const ticketPriorities = inject('ticketPriorities')
		const ticketStatuses = inject('ticketStatuses')
		const ticketController = inject('ticketController')
		const agents = inject('agents')

		return {
			user,
			tickets,
			ticketTypes,
			ticketPriorities,
			ticketStatuses,
			ticketController,
			agents,
		}
	},
	computed: {
		ticket() {
			return this.tickets[this.ticketId] || null
		}
	},
	methods: {
		createAndAssignTicketTypeFromDialog() {
			if (this.newType) {
				this.ticketController.set(this.ticketId, 'type', this.newType)
				this.closeCreateNewTicketTypeDialog();
			}
		},
		createTicketFromDialog() {
			if (this.newType) {
				this.$tickets().createType(this.newType)
				this.closeCreateNewTicketTypeDialog();
			}
		},
		closeCreateNewTicketTypeDialog() {
			this.newType = ""
			this.openCreateNewTicketTypeDialog = false
		},
		agentsAsDropdownOptions() {
			let agentItems = [];
			if (this.agents) {
				this.agents.forEach(agent => {
					agentItems.push({
						label: agent.agent_name,
						handler: () => {
							this.ticketController.set(this.ticketId, 'agent', agent.name)
						},
					});
				});
				let options = [];
				if (this.user.agent) {
					options.push({
						group: 'Myself',
						hideLabel: true,
						items: [
							{
								label: 'Assign to me',
								handler: () => {
									this.ticketController.set(this.ticketId, 'agent')
								}
							},
						],
					})
				}
				options.push({
					group: 'All Agents',
					hideLabel: true,
					items: agentItems,
				})
				return options;
			} else {
				return null;
			}
		},
		typesAsDropdownOptions() {
			let typeItems = [];
			if (this.ticketTypes) {
				this.ticketTypes.forEach(type => {
					typeItems.push({
						label: type.name,
						handler: () => {
							this.ticketController.set(this.ticketId, 'type', type.name)
						},
					});
				});
				let options = [];
				options.push({
					group: 'Create New',
					hideLabel: true,
					items: [
						{
							label: 'Create New',
							handler: () => {
								this.openCreateNewTicketTypeDialog = true
							}
						},
					],
				})
				options.push({
					group: 'All Types',
					hideLabel: true,
					items: typeItems,
				})
				return options;
			} else {
				return null;
			}
		},
		statusesAsDropdownOptions() {
			let statusItems = [];
			if (this.ticketStatuses) {
				this.ticketStatuses.forEach(status => {
					statusItems.push({
						label: status,
						handler: () => {
							this.ticketController.set(this.ticketId, 'status', status)
						},
					});
				});
				return statusItems;
			} else {
				return null;
			}
		},
		prioritiesAsDropdownOptions() {
			let typeItems = [];
			if (this.ticketPriorities) {
				this.ticketPriorities.forEach(priority => {
					typeItems.push({
						label: priority.name,
						handler: () => {
							this.ticketController.set(this.ticketId, 'priority', priority.name)
						},
					});
				});
				return typeItems;
			} else {
				return null;
			}
		},
		redirectToRoute(route) {
			window.location.href = route
		}
	}
}
</script>

<style>

</style>