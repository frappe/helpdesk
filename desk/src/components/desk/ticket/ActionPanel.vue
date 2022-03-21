<template>
	<div class="m-4 px-4 rounded shadow" v-if="ticket">
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
					<Dropdown
						v-if="agents"
						:options="agentsAsDropdownOptions()" 
						class="text-base w-full bg-gray-100 hover:bg-gray-200 px-2 cursor-pointer rounded mr-1"
					>
						<template v-slot="{ toggleAssignees }" @click="toggleAssignees" class="w-full">
							<div class="flex py-1 space-x-1 w-full items-center">
								<div class="grow">
									<div v-if="ticket.assignees.length > 0 && !updatingAssignee" class="text-left">{{ ticket.assignees[0].agent_name }}</div>
									<div v-else>
										<LoadingText v-if="updatingAssignee" />
										<div v-else class="text-base text-left text-gray-400"> assign agent </div>
									</div>
								</div>
								<div>
									<CustomIcons v-if="!updatingAssignee" name="select" class="w-4 h-4" />
								</div>
							</div>
						</template>
					</Dropdown>
				</div>
				<div class="flex flex-col space-y-2">
					<div class="text-slate-500">Status</div>
					<Dropdown
						v-if="ticketStatuses"
						:options="statusesAsDropdownOptions()" 
						class="text-base w-full bg-gray-100 hover:bg-gray-200 px-2 cursor-pointer rounded mr-1"
					>
						<template v-slot="{ toggleStatuses }" @click="toggleStatuses" class="w-full">
							<div class="flex py-1 space-x-1 w-full items-center">
								<div class="grow">
									<div v-if="ticket.status && !updatingStatus" class="text-left">{{ ticket.status }}</div>
									<div v-else>
										<LoadingText v-if="updatingStatus" />
										<div v-else class="text-base text-left text-gray-400"> set status </div>
									</div>
								</div>
								<div>
									<CustomIcons v-if="!updatingStatus" name="select" class="w-4 h-4" />
								</div>
							</div>
						</template>
					</Dropdown>
				</div>
				<div class="flex flex-col space-y-2">
					<div class="text-slate-500">Team</div>
					<Dropdown
						v-if="agentGroups"
						:options="agentGroupsAsDropdownOptions()" 
						class="text-base w-full bg-gray-100 hover:bg-gray-200 px-2 cursor-pointer rounded mr-1"
					>
						<template v-slot="{ toggleAgentGroups }" @click="toggleAgentGroups" class="w-full">
							<div class="flex py-1 space-x-1 w-full items-center">
								<div class="grow">
									<div v-if="ticket.agent_group && !updatingTeam" class="text-left">{{ ticket.agent_group }}</div>
									<div v-else>
										<LoadingText v-if="updatingTeam" />
										<div v-else class="text-base text-left text-gray-400"> set team </div>
									</div>
								</div>
								<CustomIcons v-if="!updatingTeam" name="select" class="w-4 h-4" />
							</div>
						</template>
					</Dropdown>
				</div>
				<div class="flex flex-col space-y-2">
					<div class="text-slate-500">Priority</div>
					<Dropdown
						v-if="ticketPriorities"
						:options="prioritiesAsDropdownOptions()" 
						class="text-base w-full bg-gray-100 hover:bg-gray-200 px-2 cursor-pointer rounded mr-1"
					>
						<template v-slot="{ togglePriority }" @click="togglePriority" class="w-full">
							<div class="flex py-1 space-x-1 w-full items-center">
								<div class="grow">
									<div v-if="ticket.priority && !updatingPriority" class="text-left">{{ ticket.priority }}</div>
									<div v-else>
										<LoadingText v-if="updatingPriority" />
										<div v-else class="text-base text-left text-gray-400"> set priority </div>
									</div>
								</div>
								<CustomIcons v-if="!updatingPriority" name="select" class="w-4 h-4" />
							</div>
						</template>
					</Dropdown>
				</div>
				<div class="flex flex-col space-y-2">
					<div class="text-slate-500">Type</div>
					<Dropdown
						v-if="ticketTypes"
						:options="typesAsDropdownOptions()" 
						class="text-base w-full bg-gray-100 hover:bg-gray-200 px-2 cursor-pointer rounded mr-1"
					>
						<template v-slot="{ toggleTicketTypes }" @click="toggleTicketTypes" class="w-full">
							<div class="flex py-1 space-x-1 w-full items-center">
								<div class="grow">
									<div v-if="ticket.ticket_type && !updatingTicketType" class="text-left">{{ ticket.ticket_type }}</div>
									<div v-else>
										<LoadingText v-if="updatingTicketType" />
										<div v-else class="text-base text-left text-gray-400"> set type </div>
									</div>
								</div>
								<CustomIcons v-if="!updatingTicketType" name="select" class="w-4 h-4" />
							</div>
						</template>
					</Dropdown>
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
		const agentGroups = inject('agentGroups')

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
			agentGroups,

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
							this.updatingAssignee = true;
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
									this.updatingAssignee = true;
									this.ticketController.set(this.ticketId, 'agent').then(() => {
										this.updatingAssignee = false
									})
								}
							},
						],
					})
				}
				if (agentItems.length > 0) {
					options.push({
						group: 'All Agents',
						hideLabel: true,
						items: agentItems,
					})
				}
				if (options.length == 0) {
					options.push({
						label: 'No agents found'
					})
				}
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
							this.updatingTicketType = true;
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
				if (typeItems.length > 0) {
					options.push({
						group: 'All Types',
						hideLabel: true,
						items: typeItems,
					})
				}
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
				if (statusItems.length == 0) {
					statusItems.push({
						label: 'No statuses found'
					})
				}
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
				if (typeItems.length == 0) {
					typeItems.push({
						label: 'No priorities found'
					})
				}
				return typeItems;
			} else {
				return null;
			}
		},
		agentGroupsAsDropdownOptions() {
			let groupItems = [];
			if (this.agentGroups) {
				this.agentGroups.forEach(group => {
					groupItems.push({
						label: group.name,
						handler: () => {
							this.updatingTeam = true
							this.ticketController.set(this.ticketId, 'group', group.name).then(() => {
								this.updatingTeam = false
							})
						},
					});
				});
				if (groupItems.length == 0) {
					typeItems.push({
						label: 'No team found'
					})
				}
				return groupItems;
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