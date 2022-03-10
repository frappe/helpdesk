<template>
	<div class="px-3" v-if="ticket">
		<div class="py-4 border-b space-y-3">
			<div class="text-lg font-medium">{{ `Ticket #${ticket.name}` }}</div>
			<div class="text-base space-y-2">
				<div class="flex flex-col space-y-2">
					<div class="flex space-x-2 items-center">
						<div class="text-slate-500">{{`First Response ${firstResponseStatus() ? '' : 'Due'}`}}</div>
						<div v-if="firstResponseStatus()">
							<FeatherIcon v-if="firstResponseStatus() == 'Failed'" name="x" class="stroke-red-500 w-5 h-5"/>
							<FeatherIcon v-if="firstResponseStatus() == 'Success'" name="check" class="stroke-green-500 w-5 h-5"/>
						</div>
					</div>
					<div v-if="!firstResponseStatus()">{{ getFormatedDate(ticket.response_by, 'ddd, MMM DD, YYYY HH:mm')}}</div>
				</div>
				<div class="flex flex-col space-y-2">
					<div class="flex space-x-2 items-center">
						<div class="text-slate-500">{{`Resolution ${resolutionStatus() ? '' : 'Due'}`}}</div>
						<div v-if="resolutionStatus()">
							<FeatherIcon v-if="resolutionStatus() == 'Failed'" name="x" class="stroke-red-500 w-5 h-5"/>
							<FeatherIcon v-else-if="resolutionStatus() == 'Success'" name="check" class="stroke-green-500 w-5 h-5"/>
							<Badge v-else-if="resolutionStatus() == 'Paused'" color="blue">Paused</Badge>
						</div>
					</div>
					<div v-if="!resolutionStatus()">{{ getFormatedDate(ticket.resolution_by, 'ddd, MMM DD, YYYY HH:mm') }}</div>
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
								<div v-else class="flex items-center">
									<LoadingText v-if="updatingAssignee" />
									<div class="text-base grow w-52 text-left text-gray-400"> assign agent </div>
								</div>
								<CustomIcons v-if="!updatingAssignee" name="select" class="w-4 h-4 float-right" />
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
						<template v-slot="{ toggleStatuses }" @click="toggleStatuses" class="w-full">
							<div class="w-full">
								<div class="flex w-56 py-1 hover:bg-slate-50 space-x-1">
									<div v-if="ticket.status" class="grow w-52 text-left">{{ ticket.status }}</div>
									<div v-else class="flex items-center">
										<LoadingText v-if="updatingStatus" />
										<div class="text-base grow w-52 text-left text-gray-400"> set status </div>
									</div>
								<CustomIcons v-if="!updatingStatus" name="select" class="w-4 h-4 float-right" />
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
						<template v-slot="{ togglePriority }" @click="togglePriority" class="w-full">
							<div class="flex w-56 py-1 hover:bg-slate-50 space-x-1">
								<div v-if="ticket.priority" class="grow w-52 text-left">{{ ticket.priority }}</div>
								<div v-else class="flex items-center">
									<LoadingText v-if="updatingPriority" />
									<div class="text-base grow w-52 text-left text-gray-400"> set priority </div>
								</div>
								<CustomIcons v-if="!updatingPriority" name="select" class="w-4 h-4 float-right" />
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
						<template v-slot="{ toggleTicketTypes }" @click="toggleTicketTypes" class="w-full">
							<div class="flex w-56 py-1 hover:bg-slate-50 space-x-1 items-center">
								<div v-if="ticket.ticket_type" class="grow w-52 text-left">{{ ticket.ticket_type }}</div>
								<div v-else class="flex items-center">
									<LoadingText v-if="updatingTicketType" />
									<div v-else class="text-base grow w-52 text-left text-gray-400"> set type </div>
								</div>
								<CustomIcons v-if="!updatingTicketType" name="select" class="w-4 h-4 float-right" />
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
						<div class="text-slate-500">{{ field.label }}</div>
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
import { FeatherIcon, Dropdown, Input, Dialog, Badge, LoadingText } from 'frappe-ui'
import CustomDropdown from '@/components/desk/global/CustomDropdown.vue'
import CustomIcons from '@/components/desk/global/CustomIcons.vue'
import { inject, ref } from '@vue/runtime-core'

export default {
	name: "ActionPanel",
	props: ["ticketId"],
	components: {
		Badge,
		FeatherIcon,
		Dropdown,
		CustomDropdown,
		Input,
		Dialog,
		CustomIcons,
		LoadingText
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

		const updatingTicketType = ref(false)
		const updatingAssignee = ref(false)
		const updatingPriority = ref(false)
		const updatingStatus = ref(false)
		const updatingTeam = ref(false)

		return {
			user,
			tickets,
			ticketTypes,
			ticketPriorities,
			ticketStatuses,
			ticketController,
			agents,

			updatingTicketType,
			updatingAssignee,
			updatingPriority,
			updatingStatus,
			updatingTeam
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
				this.updatingTicketType = true
				this.ticketController.set(this.ticketId, 'type', this.newType).then(() => {
					this.updatingTicketType = false
				})
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
							this.updatingAssignee = true
							this.ticketController.set(this.ticketId, 'agent', agent.name).then(() => {
								this.updatingAssignee = false
							})
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
									this.updatingAssignee = true
									this.ticketController.set(this.ticketId, 'agent').then(() => {
										this.updatingAssignee = false
									})
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
							this.updatingTicketType = true
							this.ticketController.set(this.ticketId, 'type', type.name).then(() => {
								this.updatingTicketType = false
							})
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
							this.updatingStatus = true
							this.ticketController.set(this.ticketId, 'status', status).then(() => {
								this.updatingStatus = false
							})
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
							this.updatingPriority = true
							this.ticketController.set(this.ticketId, 'priority', priority.name).then(() => {
								this.updatingPriority = false
							})
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
		},
		getFormatedDate(date, format) {
			return date ? this.$dayjs(date).format(format) : ''
		},
		firstResponseStatus() {
			if (this.ticket.first_responded_on) {
				return this.ticket.response_by > this.ticket.first_responded_on ? 'Success' : 'Failed'
			} else {
				return null
			}
		},
		resolutionStatus() {
			switch(this.ticket.agreement_status) {
				case 'Resolution Due':
					return this.ticket.resolution_by ? '' : 'Paused'
				case 'Fulfilled':
					return 'Success'
				case 'Overdue':
					return 'Failed'
				default:
					return ''


			}
		}
	}
}
</script>

<style>

</style>