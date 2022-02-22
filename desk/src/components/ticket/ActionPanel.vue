<template>
	<div class="px-3" v-if="contact && ticket">
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
		<div class="py-4 space-y-3">
			<div class="text-base space-y-2">
				<div class="flex flex-col space-y-2">
					<div class="text-slate-500">Assignee</div>
					<CustomDropdown
						v-if="$tickets().get('statuses')"
						:options="agentsAsDropdownOptions()" 
						class="text-base w-56"
					>
						<template v-slot="{ toggleAssignees }" @click="toggleAssignees" class="w-full">
							<div class="w-full">
								<div v-if="ticket.assignees.length > 0" class="flex w-56 py-1 hover:bg-slate-50 space-x-1">
									<div class="grow w-52 text-left">{{ ticket.assignees[0].agent_name }}</div>
									<FeatherIcon name="chevron-down" class="w-4 h-4 float-right" />
								</div>
								<div v-else class="flex pr-1 py-1 hover:bg-slate-50 w-56 space-x-1">
									<span class="text-base grow w-52 text-left text-gray-400"> assign agent </span>
									<FeatherIcon name="chevron-down" class="w-4 h-4 float-right" />
								</div>
							</div>
						</template>
					</CustomDropdown>
				</div>
				<div class="flex flex-col space-y-2">
					<div class="text-slate-500">Status</div>
					<CustomDropdown
						v-if="$tickets().get('statuses')"
						:options="statusesAsDropdownOptions()" 
						class="text-base w-56"
					>
						<template v-slot="{ toggleAssignees }" @click="toggleAssignees" class="w-full">
							<div class="w-full">
								<div v-if="ticket.status" class="flex w-56 py-1 hover:bg-slate-50 space-x-1">
									<div class="grow w-52 text-left">{{ ticket.status }}</div>
									<FeatherIcon name="chevron-down" class="w-4 h-4 float-right" />
								</div>
								<div v-else class="flex pr-1 py-1 hover:bg-slate-50 w-56 space-x-1">
									<span class="text-base grow w-52 text-left text-gray-400"> set status </span>
									<FeatherIcon name="chevron-down" class="w-4 h-4 float-right" />
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
						v-if="$tickets().get('priorities')"
						:options="prioritiesAsDropdownOptions()" 
						class="text-base w-56"
					>
						<template v-slot="{ toggleAssignees }" @click="toggleAssignees" class="w-full">
							<div class="w-full">
								<div v-if="ticket.priority" class="flex w-56 py-1 hover:bg-slate-50 space-x-1">
									<div class="grow w-52 text-left">{{ ticket.priority }}</div>
									<FeatherIcon name="chevron-down" class="w-4 h-4 float-right" />
								</div>
								<div v-else class="flex pr-1 py-1 hover:bg-slate-50 w-56 space-x-1">
									<span class="text-base grow w-52 text-left text-gray-400"> set priority </span>
									<FeatherIcon name="chevron-down" class="w-4 h-4 float-right" />
								</div>
							</div>
						</template>
					</CustomDropdown>
				</div>
				<div class="flex flex-col space-y-2">
					<div class="text-slate-500">Type</div>
					<CustomDropdown
						v-if="$tickets().get('types')"
						:options="typesAsDropdownOptions()" 
						class="text-base w-56"
					>
						<template v-slot="{ toggleAssignees }" @click="toggleAssignees" class="w-full">
							<div class="w-full">
								<div v-if="ticket.ticket_type" class="flex w-56 py-1 hover:bg-slate-50 space-x-1">
									<div class="grow w-52 text-left">{{ ticket.ticket_type }}</div>
									<FeatherIcon name="chevron-down" class="w-4 h-4 float-right" />
								</div>
								<div v-else class="flex pr-1 py-1 hover:bg-slate-50 w-56 space-x-1">
									<span class="text-base grow w-52 text-left text-gray-400"> set type </span>
									<FeatherIcon name="chevron-down" class="w-4 h-4 float-right" />
								</div>
							</div>
						</template>
					</CustomDropdown>
				</div>
			</div>
		</div>
	</div>
</template>

<script>
import { FeatherIcon, Dropdown } from 'frappe-ui'
import CustomDropdown from '../global/CustomDropdown.vue'

export default {
	name: "ActionPanel",
	props: ["ticket", "contact"],
	components: {
		FeatherIcon,
		Dropdown,
		CustomDropdown
	},
	methods: {
		agentsAsDropdownOptions() {
			let agentItems = [];
			if (this.$agents.get()) {
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
	}
}
</script>

<style>

</style>