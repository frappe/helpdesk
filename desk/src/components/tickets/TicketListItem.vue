<template>
	<div class="block py-4 hover:bg-gray-50 border-b">
		<div 
			v-if="ticket"
			class="group flex items-center justify-between sm:justify-start font-light pl-4 pr-8"
		>
			<div
				class="mr-4"
			>
				<Input type="checkbox" value="" />
			</div>
			<router-link 
				:to="`/tickets/${ticket.name}`"
				class="sm:w-9/12"
			>
				<div class="flex flex-col space-y-1">
					<div class="flex items-center">
						<div class="text-base font-medium">{{ ticket.subject }}</div>
						<div class="ml-1 text-base text-slate-400">#{{ ticket.name }}</div>
						<div class="ml-1">
							<Badge :color="getResolutionBadgeColor(ticket.resolution_by, ticket.agreement_status)">
								{{ getResolutionDueIn(ticket.resolution_by, ticket.agreement_status) }}
							</Badge>
						</div>
					</div>
					<div class="flex items-center">
						<div class="flex">
							<FeatherIcon class="w-4 h-4 stroke-slate-400" name="user" />
							<div class="ml-1 text-base">{{ ticket.contact }}</div>
						</div>
					</div>
				</div>
			</router-link>
			<div class="flex items-center justify-between sm:justify-start font-light sm:w-6/12">
				<Dropdown 
					v-if="types"
					placement="left" 
					:options="typesAsDropdownOptions()" 
					:dropdown-width-full="true"
					class="text-base sm:w-4/12"
				>
					<template v-slot="{ toggleTypes }">
						<div  
							class="w-full"
							@click="toggleTypes"
						>
							<div v-if="ticket.ticket_type" class="flex items-center">
								<div>
									<FeatherIcon class="w-3 h-3 stroke-slate-400" name="tag" />
								</div>
								<div class="ml-1 text-gray-500">
									{{ ticket.ticket_type }}
								</div>
								<FeatherIcon class="w-2 h-2  ml-1 hidden group-hover:block" name="chevron-down"/>
							</div>
							<div v-else class="hidden group-hover:block">
								<span class="text-base text-gray-400"> set type </span>
							</div>
						</div>
					</template>
				</Dropdown>
				<Dropdown
					v-if="priorities"
					placement="left" 
					:options="prioritiesAsDropdownOptions()" 
					:dropdown-width-full="true"
					class="text-base sm:w-4/12"
				>
					<template v-slot="{ togglePriority }">
						<div class="w-full cursor-pointer">
							<div 
								v-if="ticket.priority"
								@click="togglePriority"	
								class="flex items-center"
							>
								<FeatherIcon 
									class="w-3 h-3" 
									:name="getIconBasedOnPriority(ticket.priority)"
								/>
								<div class="ml-1 text-gray-500">{{ ticket.priority }}</div>
								<FeatherIcon class="w-2 h-2  ml-1 hidden group-hover:block" name="chevron-down"/>
							</div>
							<div v-else class="hidden group-hover:block">
								<span class="text-base text-gray-400"> set priority </span>
							</div>
						</div>
					</template>
				</Dropdown> 
				<Dropdown
					v-if="this.statuses"
					placement="left" 
					:options="statusesAsDropdownOptions()" 
					:dropdown-width-full="true"
					class="text-base sm:w-4/12"
				>
					<template v-slot="{ toggleStatuses }">
						<div class="w-full cursor-pointer">
							<div 
								v-if="ticket.status"
								@click="toggleStatuses"	
								class="flex items-center"
							>
								<FeatherIcon class="w-2 h-2 stroke-transparent" :class="getBadgeColorBasedOnStatus(ticket.status)" name="circle"/>
								<div class="ml-1 text-gray-500">{{ ticket.status }}</div>
								<FeatherIcon class="w-2 h-2  ml-1 hidden group-hover:block" name="chevron-down"/>

							</div>
							<div v-else class="hidden group-hover:block">
								<span class="text-base text-gray-400"> set status </span>
							</div>
						</div>
					</template>
				</Dropdown>
				<div class="hidden sm:w-1/12 text-base text-gray-600 sm:block">
					<div class="flex items-center">
						<div>
							<FeatherIcon class="w-3 h-3 stroke-slate-400" name="edit-2"/>
						</div>
						<div class="ml-1">
							{{ $dayjs(ticket.modified).fromNow() }}
						</div>
					</div>
				</div>
			</div>
			<div class="sm:w-1/12">
				<Dropdown
					v-if="this.agents"
					placement="right" 
					:options="agentsAsDropdownOptions()" 
					:dropdown-width-full="true"
					class="text-base flex flex-row-reverse"
				>
					<template v-slot="{ toggleAssignees }">
						<div  
							@click="toggleAssignees"
						>
							<div v-if="ticket.assignees.length > 0">
								<div v-for="assignee in ticket.assignees" :key="assignee">
									<Avatar class="w-4 h-4" :label="assignee.agent_name" :imageURL="assignee.image" />
								</div>
							</div>
							<div v-else class="hidden group-hover:block">
								<span class="text-base text-gray-400"> assign agent </span>
							</div>
						</div>
					</template>
				</Dropdown>
			</div>
		</div>
		<div class="transform translate-y-2"/>
	</div>
</template>

<script>
import { Badge, Dropdown, Input, FeatherIcon, Avatar } from 'frappe-ui'

export default {
	name: 'TicketListItem',
	props: ['ticket'],
	inject: ['agents', 'types', 'statuses', 'priorities'],
	components: {
		Input,
		Badge,
		Dropdown,
		FeatherIcon,
		Avatar
	},
	data() {
		return {
			ticketRefreshed: false,
			localTicket: null,
		}
	},
	methods: {
		getBadgeColorBasedOnStatus(status) {
			if (['Open'].includes(status)) {
				return 'fill-green-500'
			}
			if (['Closed', 'Resolved'].includes(status)) {
				return 'fill-red-500'
			}
			if (['Replied'].includes(status)) {
				return 'fill-yellow-500'
			}
			if (['On Hold'].includes(status)) {
				return 'fill-blue-500'
			}
		},
		getColorBasedOnPriority(priority, type) {
			let sufix = '';
			if (type == 'icon') { 
				sufix = 'stroke';
			} else if (type == 'text') {
				sufix = 'text';
			}
			let color = '';
			if (priority == 'High') {
				color = 'red-500'
			} else if (priority == 'Medium') {
				color = 'yellow-500'
			} else if (priority == "Low") {
				color = 'green-500'
			}

			return sufix ? sufix + '-' + color : color;
		},
		getIconBasedOnPriority(priority) {
			if (priority == 'High') {
				return 'arrow-up'
			}
			if (priority == 'Medium') {
				return 'arrow-up'
			}
			if (priority == "Low") {
				return 'arrow-down'
			}
		},
		agentsAsDropdownOptions() {
			let agentItems = [];
			if (this.agents) {
				this.$agents.get().forEach(agent => {
					agentItems.push({
						label: agent.agent_name,
						handler: () => {
							this.$tickets(this.ticket.name).assignAgent(agent.name)
						},
					});
				});
				let options = [];
				if (this.$user.get().agent) {
					options.push({
						group: 'Myself',
						hideLabel: true,
						items: [
							{
								label: 'Assign to me',
								handler: () => {
									this.$tickets(this.ticket.name).assignAgent()
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
			if (this.$tickets().get("types")) {
				this.$tickets().get("types").forEach(type => {
					typeItems.push({
						label: type,
						handler: () => {
							this.$tickets(this.ticket.name).assignType(type)
						},
					});
				});
				return typeItems;
			} else {
				return null;
			}
		},
		statusesAsDropdownOptions() {
			let statusItems = [];
			if (this.$tickets().get("statuses")) {
				this.$tickets().get("statuses").forEach(status => {
					statusItems.push({
						label: status,
						handler: () => {
							this.$tickets(this.ticket.name).assignStatus(status)
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
			if (this.$tickets().get("priorities")) {
				this.$tickets().get("priorities").forEach(priority => {
					typeItems.push({
						label: priority,
						handler: () => {
							this.$tickets(this.ticket.name).assignPriority(priority)
						},
					});
				});
				return typeItems;
			} else {
				return null;
			}
		},
		getResolutionDueIn(resolutionBy, agreementStatus) {
			if (["Fulfilled", "Overdue"].includes(agreementStatus)) {
				return agreementStatus;
			}
			let resolutionString = this.$dayjs().to(resolutionBy);
			return !resolutionString.includes("in") ? "Overdue" : "Due " + resolutionString;
		},
		getResolutionBadgeColor(resolutionBy, agreementStatus) {
			let resolutionString = this.$dayjs().to(resolutionBy);
			return !resolutionString.includes("in") ? "red" : (agreementStatus == "Fulfilled" ? "green" : "");
		}
	}
}
</script>

<style>

</style>