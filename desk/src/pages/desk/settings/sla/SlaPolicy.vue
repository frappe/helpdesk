<template>
	<div class="p-5 overflow-auto h-full">
		<div v-if="!isNew && ($resources.getSlaPolicy.loading || $resources.updateServicePolicy.loading)">
			<LoadingText text="Fetching policy..." />
		</div>
		<div v-else>
			<div class="flow-root mb-4">
				<div class="float-left">
					<div v-if="!$resources.renameServicePolicy.loading">
						<div v-if="!editingName" class="flex space-x-2 items-center" :class="slaPolicyName != 'Default' ? 'cursor-pointer' : ''" @click="editPolicyName()">
							<div class="font-semibold">{{ slaPolicyName }}</div>
							<FeatherIcon v-if="slaPolicyName != 'Default'" class="w-3 h-3" name="edit-2" />
						</div>
						<div v-else class="flex space-x-2 items-center">
							<Input v-model="tempSlaPolicyName" type="text" placeholder="Enter Policy Name" />
							<FeatherIcon class="w-4 h-4 cursor-pointer" name="x" @click="() => {
								editingName = false
								tempSlaPolicyName = slaPolicyName
							}" />
						</div>
					</div>
					<div v-else>
						<LoadingText text="Renaming..." />
					</div>
				</div>
				<div class="float-right">
					<div class="flex space-x-2 items-center">
						<Button appearance="secondary" @click="cancel()">Cancel</Button>
						<Button v-if="isNew" appearance="primary" @click="create()">Create</Button>
						<Button v-else appearance="primary" @click="save()">Save</Button>
					</div>
				</div>
			</div>
			<div class="mb-5">
				<div class="flex space-x-2 items-center">
					<div class="text-base font-semibold">Rules</div>
				</div>
				<div>
					<div class="text-base">
						<div class="flex text-gray-600 py-4 border-b">
							<div class="w-2/12">Priority</div>
							<div class="w-1/12">Default</div>
							<div class="w-3/12 text-right">First Response Time</div>
							<div class="w-3/12 text-right">Resolution Time</div>
						</div>
						<div v-for="(rule, index) in rules" :key="rule.priority">
							<div class="flex text-gray-900 py-2 items-center" :class="index < rules.length - 1 ? 'border-b' : ''">
								<div class="w-2/12">
									<Dropdown
										v-if="ticketPriorities"
										:options="prioritiesAsDropdownOptions(index)" 
										class="text-base w-full cursor-pointer"
									>
										<template v-slot="{ togglePriority }" @click="togglePriority" class="w-full">
											<div class="flex items-center space-x-2">
												<div class="text-left">{{ rule.priority }}</div>
												<!-- <FeatherIcon name="chevron-down" class="h-4 w-4" /> -->
											</div>
										</template>
									</Dropdown>
								</div>
								<div class="w-1/12">
									<Switch
										:class="rule.default ? 'bg-blue-500' : 'bg-slate-300'"
										class="relative inline-flex items-center h-6 rounded-full w-11"
										@click="changeDefaultPriority(index)"
									>
										<span
											:class="rule.default ? 'translate-x-6' : 'translate-x-1'"
											class="inline-block w-4 h-4 transform bg-white rounded-full"
										/>
									</Switch>
								</div>
								<div class="w-3/12 flex flex-row-reverse">
									<TimeDurationInput v-model="rule.firstResponseTime"/>
								</div>
								<div class="w-3/12 flex flex-row-reverse">
									<TimeDurationInput v-model="rule.resolutionTime"/>
								</div>
								<div class="w-1/12 flex flex-row-reverse" v-if="rules.length > 1">
									<FeatherIcon name="trash" class="cursor-pointer h-5 w-5 stroke-red-500 hover:stroke-red-600" @click="removeRule(index)"/>
								</div>
							</div>
						</div>
					</div>
					<div class="mb-2"></div>
					<Button @click="addRule()">Add Rule</Button>
				</div>
			</div>
			<div>
				<div class="flex space-x-2 items-center mb-3">
					<div class="text-base font-semibold">Working Hours</div>
				</div>
				<div>
					<p class="text-base text-gray-700">Choose the days in a week, and start and end times to set as working hours. </p>
					<div class="py-4 space-y-3 text-gray-900">
						<div v-for="workingHour in workingHours" :key="workingHour.workday">
							<div class="flex text-base items-center h-7">
								<div class="w-2/12">{{ workingHour.workday }}</div>
								<div class="w-2/12 flex space-x-2 items-center">
									<Switch
										v-model="workingHour.enabled"
										:class="workingHour.enabled ? 'bg-blue-500' : 'bg-slate-300'"
										class="relative inline-flex items-center h-6 rounded-full w-11"
									>
										<span
											:class="workingHour.enabled ? 'translate-x-6' : 'translate-x-1'"
											class="inline-block w-4 h-4 transform bg-white rounded-full"
										/>
										<span class="sr-only">{{ `${workingHour.enabled ? 'Open' : 'Closed' }`}}</span>
									</Switch>
									<div>{{ workingHour.enabled ? 'Open' : 'Closed' }}</div>
								</div>
								<div v-if="workingHour.enabled" class="w-6/12 flex space-x-4 items-center">
									<input class="rounded py-1 bg-gray-200 border-0 text-base w-[6.4rem] px-1" type="time" v-model="workingHour.from">
									<div class="text-gray-600">TO</div>
									<input class="rounded py-1 bg-gray-200 border-0 text-base w-[6.4rem] px-1" type="time" v-model="workingHour.to">
								</div>
							</div>
						</div>
					</div>
					<div class="space-y-4">
						<Input class="w-6/12" label="Holidays on" type="text" value="" placeholder="" />
						<Input label="Conditions" type="textarea" value="" placeholder="" />
					</div>
				</div>
				<div class="mt-5 flow-root">
					<div class="float-left">
						<Button appearance="secondary" @click="cancel()">Cancel</Button>
					</div>
					<div class="float-right">
						<Button v-if="isNew" appearance="primary" @click="create()">Create</Button>
						<Button v-else appearance="primary" @click="save()">Save</Button>
					</div>
				</div>
			</div>
		</div>
	</div>
</template>

<script>
import { FeatherIcon, Input, LoadingText, Dropdown } from 'frappe-ui'
import TimeDurationInput from '@/components/desk/global/TimeDurationInput.vue'
import { Switch } from '@headlessui/vue'
import { inject, ref } from 'vue'

export default {
	name: 'SlaPolicy',
	props: ['slaId'],
	components: {
		FeatherIcon,
		Input,
		LoadingText,
		Dropdown,
		TimeDurationInput,
		Switch
	},
	setup() {
		const isNew = ref(false)

		const slaPolicyName = ref('')
		const editingName = ref(false)
		const tempSlaPolicyName = ref('')

		const rules = ref([])
		const workingHours = ref([])

		const ticketPriorities = inject('ticketPriorities')

		const selectedSetting = inject('selectedSetting')

		return {
			isNew, 
			slaPolicyName, 
			tempSlaPolicyName, 
			editingName, 
			rules, 
			workingHours, 
			ticketPriorities,
			selectedSetting
		}
	},
	activated() {
		this.selectedSetting = 'Support Policies' // TODO: use a better logic for this
		this.isNew = (this.$route.name === 'NewSlaPolicy')
		this.editingName = false
		if (this.isNew) {
			this.setDefaultValues()
		} else {
			this.$resources.getSlaPolicy.fetch()
		}
	},
	deactivated() {

	},
	resources: {
		getSlaPolicy() {
			return {
				method: 'frappe.client.get',
				params: {
					doctype: 'Service Level Agreement',
					name: this.slaId,
					fields: ["*"]
				},
				onSuccess: (data) => {
					this.slaPolicyName = data.name
					this.rules = data.priorities.map(priority => {
						return {
							priority: priority.priority,
							default: priority.default_priority,
							firstResponseTime: priority.response_time,
							resolutionTime: priority.resolution_time
						}
					})
					this.workingHours = data.support_and_resolution.map(workingHour => {
						return {
							workday: workingHour.workday,
							enabled: true,
							from: workingHour.start_time,
							to: workingHour.end_time 
						}
					})

					let weekdays = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
					weekdays.forEach(day => {
						if (!this.workingHours.find(x => x.workday == day)) {
							this.workingHours.push({
								workday: day,
								enabled: false,
								from: '00:00:00',
								to: '00:00:00' 
							})
						}
					})

					this.workingHours = this.workingHours.sort((a, b) => {
						return weekdays.findIndex(x => x == a.workday) - weekdays.findIndex(x => x == b.workday)
					})
				},
				onFailure: (error) => {
					console.log(error)
				}
			}
		},
		updateServicePolicy() {
			return {
				method: 'frappe.client.set_value',
				onSuccess: () => {
					console.log('here 2 -')
				},
				onFailure: (error) => {
					console.log(error)
				}
			}
		},
		createNewServicePolicy() {
			return {
				method: 'frappe.client.insert',
				onSuccess: () => {
					this.$router.push({
						name: 'SlaPolicies'
					})
				}
			}
		},
		renameServicePolicy() {
			return {
				method: 'frappe.client.rename_doc',
				onSuccess: (data) => {
					console.log(data)
				}
			}
		}
	},
	computed: {
		priorities() {
			return this.rules.map(rule => {
				return {
					priority: rule.priority,
					default_priority: rule.default,
					response_time: rule.firstResponseTime,
					resolution_time: rule.resolutionTime,
				}
			})
		},
		supportAndResolution() {
			return this.workingHours.map(workingHour => {
				if (workingHour.enabled) {
					return {
						workday: workingHour.workday,
						start_time: workingHour.from,
						end_time: workingHour.to
					}
				}
			}).filter(x => x)
		},
	},
	methods: {
		setDefaultValues() {
			this.slaPolicyName = 'New Service Policy'
			this.tempSlaPolicyName = this.slaPolicyName

			this.rules = [
				{priority: 'Urgent', default: false, firstResponseTime: 1 * 3600, resolutionTime: 2 * 3600},
				{priority: 'High', default: false, firstResponseTime: 2 * 3600, resolutionTime: 4 * 3600},
				{priority: 'Low', default: true, firstResponseTime: 12 * 3600, resolutionTime: 24 * 3600}
			]
			this.workingHours = [
				{workday: 'Monday', enabled: true, from: '09:00', to: '17:00'},
				{workday: 'Tuesday', enabled: true, from: '09:00', to: '17:00'},
				{workday: 'Wednesday',enabled: true, from: '09:00', to: '17:00'},
				{workday: 'Thursday', enabled: true, from: '09:00', to: '17:00'},
				{workday: 'Friday', enabled: true, from: '09:00', to: '17:00'},
				{workday: 'Saturday', enabled: false, from: '09:00', to: '17:00'},
				{workday: 'Sunday', enabled: false, from: '09:00', to: '17:00'},
			]
		},
		editPolicyName() {
			if (this.slaPolicyName != 'Default') {
				this.tempSlaPolicyName = this.slaPolicyName
				this.editingName = true
			}
		},
		changeDefaultPriority(index) {
			this.rules.forEach((rule, i) => {
				if (i == index) {
					rule.default = !rule.default
				} else {
					rule.default = false
				}
			})
		},
		addRule() {
			this.rules.push({priority: 'Low', default: false, firstResponseTime: 12 * 3600, resolutionTime: 24 * 3600})
		},
		removeRule(index) {
			if (this.rules.length > 1) {
				if (this.rules[index].default) {
					if(index == 0) {
						this.rules[this.rules.length - 1].default = true
					} else {
						this.rules[index - 1].default = true
					}
				}

				this.rules.splice(index, 1)
			}
		},
		rename() {
			// TODO: once Service level agreement is renamable uncomment this block
			// return this.$resources.renameServicePolicy.submit({
			// 	doctype: "Service Level Agreement",
			// 	old_name: this.slaPolicyName,
			// 	new_name: this.tempSlaPolicyName
			// })
		},
		create() {
			this.$resources.createNewServicePolicy.submit({
				doc: {
					doctype: 'Service Level Agreement',
					service_level: this.tempSlaPolicyName,
					priorities: this.priorities,
					support_and_resolution: this.supportAndResolution,
					document_type: 'Ticket',
					holiday_list: 'Default',	// TODO: use the one from inputs
					sla_fulfilled_on: [
						{status: 'Resolved'},
						{status: 'Closed'}
					],
					pause_sla_on: [
						{status: 'Replied'},
					],
					enabled: true
				},
			})
		},
		save() {
			this.$resources.updateServicePolicy.submit({
				doctype: 'Service Level Agreement',
				name: this.slaPolicyName,
				fieldname: {
					priorities: this.priorities,
					support_and_resolution: this.supportAndResolution,
				}
			}).then(() => {
				if (this.slaPolicyName != this.tempSlaPolicyName) {
					this.rename()
				}
			})
		},
		cancel() {
			if (!this.isNew) {
				this.editingName = false
				this.$resources.getSlaPolicy.fetch()
			} else {
				this.$router.push({
					name: 'SlaPolicies'
				})
			}
		},
		prioritiesAsDropdownOptions(index) {
			let priorityItems = [];
			if (this.ticketPriorities) {
				this.ticketPriorities.forEach(priority => {
					priorityItems.push({
						label: priority.name,
						handler: () => {
							this.rules[index].priority = priority.name
						},
					});
				});
				return priorityItems;
			} else {
				return null;
			}
		},
	},
}
</script>

<style>

</style>