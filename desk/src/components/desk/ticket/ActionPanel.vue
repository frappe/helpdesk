<template>
	<div v-if="ticket">
		<div class="pl-[19px] pr-[17px] pt-[18px] pb-[28px] border-b border-dashed">
			<div class="flex flex-row pb-[15px]">
				<div class="grow"><span class="text-[16px] font-normal text-gray-500">Ticket</span> <span class="text-[15px] font-semibold">{{ `#${ticket.name}` }}</span></div>
				<div class="w-[88.54px] select-none">
					<div v-if="false" class="fixed border-[#38A160] border-[#FF7C36] border-[#E24C4C] text-[#38A160] text-[#FF7C36] text-[#E24C4C]"></div>
					<div class="absolute w-[88.54px] flex flex-row">
						<div class="grow"></div>
						<div class="shrink-0">
							<div 
								class="bg-white border px-[8px] rounded-[10px] h-fit cursor-pointer w-fit"
								:class="getStatusStyle(ticket.status)" 
								@click="toggleStatuese = !toggleStatuese"
								v-on-outside-click="() => { toggleStatuese = false }"
							>
								<div v-if="!updatingStatus" class="flex flex-row items-center h-[20px] space-x-[7px]">
									<div class="text-[10px] uppercase grow">{{ ticket.status }}</div>
									<div>
										<FeatherIcon name="chevron-down" class="h-3 stroke-gray-500" />
									</div>
								</div>
								<div v-else>
									<div class="text-[10px] h-[20px] flex flex-row items-center text-gray-500">Updating...</div>
								</div>
							</div>
							<div v-if="toggleStatuese">
								<div class="rounded-[10px] shadow bg-white py-[4px] space-y-[4px] mt-[3px] absolute z-50">
									<div v-for="status in ['Open', 'Replied', 'Resolved', 'Closed']" :key="status">
										<div 
											class="px-[8px] hover:bg-gray-50 hover:text-gray-900 cursor-pointer text-[10px] text-gray-600 mx-[4px] rounded-[6px] py-[4px] w-[95px]"
											@click="updateStatus(status)"
										> 
											{{ status }} 
										</div>
									</div>
								</div>
							</div>
						</div>

						</div>
				</div>
			</div>
			<div class="text-base space-y-[11px]">
				<div class="flex flex-col space-y-[2px]">
					<div class="flex flex-row space-x-[5.33px] items-center">
						<div class="text-gray-600 text-[12px]"> First Response Due </div>
						<CustomIcons v-if="firstResponseStatus()" :name="{Success: 'sla-pass', Failed: 'sla-fail'}[firstResponseStatus()]" class="w-[16px] h-[16px]"/>
					</div>
					<div class="font-normal text-gray-900">{{ getFormatedDate(ticket.response_by, 'ddd, MMM DD, YYYY HH:mm')}}</div>
				</div>
				<div class="flex flex-col space-y-[2px]">
					<div class="flex flex-row space-x-[5.33px] items-center">
						<div class="text-gray-600 text-[12px]"> Resolution Due </div>
						<CustomIcons v-if="resolutionStatus() != 'Paused'" :name="{Success: 'sla-pass', Failed: 'sla-fail'}[resolutionStatus()]" class="w-[16px] h-[16px]"/>
						<Badge v-else color="blue">Paused</Badge>
					</div>
					<div class="font-normal text-gray-900">{{ getFormatedDate(ticket.resolution_by, 'ddd, MMM DD, YYYY HH:mm') }}</div>
				</div>
			</div>
		</div>
		<span class="dot fixed ml-[-1px] mt-[-10.5px] bg-gray-50 border-r border-t border-b"></span>
		<span class="dot rotate-180 fixed ml-[241.5px] mt-[-10.5px] bg-white border-r border-t border-b"></span>
		<div class="px-[19px] py-[28px]">
			<div class="text-base space-y-[12px]">
				<div class="flex flex-col space-y-[8px]">
					<div class="text-gray-600 font-normal text-[12px]">Assignee</div>
					<Dropdown
						v-if="agents"
						:options="agentsAsDropdownOptions()" 
						class="text-base font-normal w-[213px] bg-gray-50 hover:bg-gray-100 pl-[9px] pr-[9.3px] cursor-pointer rounded-[6px]"
					>
						<template v-slot="{ toggleAssignees }" @click="toggleAssignees" class="w-full">
							<div class="flex flex-row py-1 space-x-1 items-center w-full">
								<div class="grow">
									<div v-if="ticket.assignees.length > 0 && !updatingAssignee" class="flex flex-row text-left space-x-2">
										<CustomAvatar :label="ticket.assignees[0].agent_name" :imageURL="ticket.assignees[0].image" size="xs" />
										<div>{{ ticket.assignees[0].agent_name }}</div>
									</div>
									<div v-else>
										<LoadingText v-if="updatingAssignee" />
										<div v-else class="text-base text-left text-gray-400"> assign agent </div>
									</div>
								</div>
								<div>
									<CustomIcons v-if="!updatingAssignee" name="select" class="w-[12px] h-[12px] stroke-gray-500" />
								</div>
							</div>
						</template>
					</Dropdown>
				</div>
				<div class="flex flex-col space-y-[8px]">
					<div class="text-gray-600 font-normal text-[12px]">Type</div>
					<Dropdown
						v-if="ticketTypes"
						:options="typesAsDropdownOptions()" 
						class="text-base font-normal w-[213px] bg-gray-50 hover:bg-gray-100 pl-[9px] pr-[9.3px] cursor-pointer rounded-[6px]"
					>
						<template v-slot="{ toggleTicketTypes }" @click="toggleTicketTypes" class="w-full">
							<div class="flex flex-row py-1 space-x-1 items-center w-full">
								<div class="grow">
									<div v-if="ticket.ticket_type && !updatingTicketType" class="text-left">{{ ticket.ticket_type }}</div>
									<div v-else>
										<LoadingText v-if="updatingTicketType" />
										<div v-else class="text-base text-left text-gray-400"> set type </div>
									</div>
								</div>
								<div>
									<CustomIcons v-if="!updatingTicketType" name="select" class="w-[12px] h-[12px] stroke-gray-500" />
								</div>
							</div>
						</template>
					</Dropdown>
				</div>
				<div class="flex flex-col space-y-[8px]">
					<div class="text-gray-600 font-normal text-[12px]">Team</div>
					<Dropdown
						v-if="agentGroups"
						:options="agentGroupsAsDropdownOptions()" 
						class="text-base font-normal w-[213px] bg-gray-50 hover:bg-gray-100 pl-[9px] pr-[9.3px] cursor-pointer rounded-[6px]"
					>
						<template v-slot="{ toggleAgentGroups }" @click="toggleAgentGroups" class="w-full">
							<div class="flex flex-row py-1 space-x-1 items-center w-full">
								<div class="grow">
									<div v-if="ticket.agent_group && !updatingTeam" class="text-left">{{ ticket.agent_group }}</div>
									<div v-else>
										<LoadingText v-if="updatingTeam" />
										<div v-else class="text-base text-left text-gray-400"> set team </div>
									</div>
								</div>
								<div>
									<CustomIcons v-if="!updatingTeam" name="select" class="w-[12px] h-[12px] stroke-gray-500" />
								</div>
							</div>
						</template>
					</Dropdown>
				</div>
				<div class="flex flex-col space-y-[8px]">
					<div class="text-gray-600 font-normal text-[12px]">Priority</div>
					<Dropdown
						v-if="ticketPriorities"
						:options="prioritiesAsDropdownOptions()" 
						class="text-base font-normal w-[213px] bg-gray-50 hover:bg-gray-100 pl-[9px] pr-[9.3px] cursor-pointer rounded-[6px]"
					>
						<template v-slot="{ togglePriority }" @click="togglePriority" class="w-full">
							<div class="flex flex-row py-1 space-x-1 items-center w-full">
								<div class="grow">
									<div v-if="ticket.priority && !updatingPriority" class="text-left">{{ ticket.priority }}</div>
									<div v-else>
										<LoadingText v-if="updatingPriority" />
										<div v-else class="text-base text-left text-gray-400"> set priority </div>
									</div>
								</div>
								<div>
									<CustomIcons v-if="!updatingPriority" name="select" class="w-[12px] h-[12px] stroke-gray-500" />
								</div>
							</div>
						</template>
					</Dropdown>
				</div>
				<Input label="Notes" type="textarea" v-model="ticket.notes" class="text-gray-600" @change="(newValue) => { ticketController.set(this.ticketId, 'notes', newValue) }" />
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
import CustomAvatar from '@/components/global/CustomAvatar.vue'
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
		CustomAvatar,
		LoadingText
	},
	data() {
		return {
			openCreateNewTicketTypeDialog: false,
			newType: "",
		}
	},
	setup() {
		const viewportWidth = inject('viewportWidth')

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

		const toggleStatuese = ref(false)

		const notes = ref('')

		return {
			viewportWidth,

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
			updatingTeam,
			toggleStatuese,

			notes
		}
	},
	computed: {
		ticket() {
			return this.tickets[this.ticketId] || null
		}
	},
	methods: {
		updateNotes(value) {
			this.ticketController.set(this.ticketId, 'notes', value)
		},
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
				this.ticketController.new('type', this.newType)
				this.closeCreateNewTicketTypeDialog();
			}
		},
		closeCreateNewTicketTypeDialog() {
			this.newType = ""
			this.openCreateNewTicketTypeDialog = false
		},
		updateStatus(status) {
			this.updatingStatus = true
			this.ticketController.set(this.ticketId, 'status', status).then(() => {
				this.updatingStatus = false
			})
		},
		getStatusStyle(status) {
			const color = {Open: '#38A160', Replied: '#FF7C36', Resolved: '#E24C4C', Closed: '#E24C4C'}[status]
			return `border-[${color}] text-[${color}]`
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
					groupItems.push({
						label: 'No team found'
					})
				}
				return groupItems;
			} else {
				return null;
			}
		},
		redirectToRoute(route) {
			if (route) {
				window.location.href = route
			}
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
	.dot {
		height: 21px;
		width: 10.5px;
		border-radius: 0 10.5px 10.5px 0;
		display: inline-block;
	}
</style>