<template>
	<div class="p-5 overflow-auto h-full">
		<div v-if="!isNew && $resources.getSlaPolicy.loading">
			<LoadingText text="Fetching policy..." />
		</div>
		<div v-else>
			<div class="flow-root mb-4">
				<div class="float-left">
					<div v-if="!editingName" class="flex space-x-2 items-center cursor-pointer" @click="editPolicyName()">
						<div class="font-semibold">{{ slaPolicyName }}</div>
						<FeatherIcon class="w-3 h-3" name="edit-2" />
					</div>
					<div v-else class="flex space-x-2 items-center">
						<Input v-model="tempSlaPolicyName" type="text" placeholder="Enter Policy Name" />
						<FeatherIcon class="w-4 h-4 cursor-pointer" name="x" @click="() => {editingName = false}" />
					</div>
				</div>
				<div class="float-right">
					<div class="flex space-x-2 items-center">
						<Button appearance="secondary">Cancel</Button>
						<Button appearance="primary">Save</Button>
					</div>
				</div>
			</div>
			<div class="mb-5">
				<div class="flex space-x-2 items-center mb-3 cursor-pointer" @click="() => {expandRules = !expandRules}">
					<div class="text-base font-semibold">Rules</div>
					<FeatherIcon :name="expandRules ? 'chevron-up' : 'chevron-down'" class="h-4 w-4" />
				</div>
				<div v-if="expandRules">
					<div class="text-base">
						<div class="flex text-gray-600 py-2 border-b">
							<div class="w-2/12">Priority</div>
							<div class="w-3/12 text-right">First Response Time</div>
							<div class="w-3/12 text-right">Resolution Time</div>
							<div class="w-2/12 text-right">Marker</div>
						</div>
						<div v-for="(rule, index) in rules" :key="rule.priority">
							<div class="flex text-gray-900 py-2" :class="index < rules.length - 1 ? 'border-b' : ''">
								<div class="w-2/12">{{ rule.priority }}</div>
								<div class="w-3/12 flex flex-row-reverse">
									<TimeDurationInput v-model="rule.firstResponseTime"/>
								</div>
								<div class="w-3/12 flex flex-row-reverse">
									<TimeDurationInput v-model="rule.resolutionTime"/>
								</div>
								<div class="w-2/12 text-right">{{ rule.marker }}</div>
							</div>
						</div>
					</div>
					<div class="mb-3"></div>
					<Button>Add Target</Button>
				</div>
			</div>
			<div>
				<div class="flex space-x-2 items-center mb-3 cursor-pointer" @click="() => {expandWorkingHours = !expandWorkingHours}">
					<div class="text-base font-semibold">Working Hours</div>
					<FeatherIcon :name="expandWorkingHours ? 'chevron-up' : 'chevron-down'" class="h-4 w-4" />
				</div>
				<div v-if="expandWorkingHours">
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
				<div class="mt-5 flow-root" v-if="expandWorkingHours || expandRules">
					<div class="float-left">
						<Button appearance="secondary">Cancel</Button>
					</div>
					<div class="float-right">
						<Button appearance="primary">Save</Button>
					</div>
				</div>
			</div>
		</div>
	</div>
</template>

<script>
import { FeatherIcon, Input, LoadingText } from 'frappe-ui'
import TimeDurationInput from '@/components/desk/global/TimeDurationInput.vue'
import { Switch } from '@headlessui/vue'
import { ref } from 'vue'

export default {
	name: 'SlaPolicy',
	props: ['slaId'],
	components: {
		FeatherIcon,
		Input,
		LoadingText,
		TimeDurationInput,
		Switch
	},
	setup(props) {
		const isNew = props.slaId === 'new' // TODO: this is a hacky solution, will need to change in the future
		// TODO: fetch the sla policy if slaId != new
		const slaPolicyName = ref('')
		const editingName = ref(false)
		const tempSlaPolicyName = ref('')

		const rules = ref([])
		const workingHours = ref({})

		const expandRules = ref(true)
		const expandWorkingHours = ref(true)

		if (isNew) {
			slaPolicyName.value = 'New Service Policy'
			rules.value = [
				{priority: 'Urgent', firstResponseTime: 1, resolutionTime: 2, marker: null},
				{priority: 'High', firstResponseTime: 2, resolutionTime: 4, marker: 'up-arrow'},
				{priority: 'Low', firstResponseTime: 12, resolutionTime: 24, marker: 'down-arrow'}
			]
			workingHours.value = [
				{workday: 'Monday', enabled: true, from: '09:00', to: '17:00'},
				{workday: 'Tuesday', enabled: true, from: '09:00', to: '17:00'},
				{workday: 'Wednesday',enabled: true, from: '09:00', to: '17:00'},
				{workday: 'Thursday', enabled: true, from: '09:00', to: '17:00'},
				{workday: 'Friday', enabled: true, from: '09:00', to: '17:00'},
				{workday: 'Saturday', enabled: false, from: '09:00', to: '17:00'},
				{workday: 'Sunday', enabled: false, from: '09:00', to: '17:00'},
			]
		}

		return {
			isNew, 
			slaPolicyName, 
			tempSlaPolicyName, 
			editingName, 
			rules, 
			workingHours, 
			expandWorkingHours, 
			expandRules 
		}
	},
	resources: {
		getSlaPolicy() {
			if (!this.isNew) {
				return {
					method: 'frappe.client.get',
					params: {
						doctype: 'Service Level Agreement',
						name: this.slaId,
						fields: ["*"]
					},
					auto: true,
					onSuccess: (data) => {
						this.slaPolicyName = data.name
						this.rules = data.priorities.map(priority => {
							return {
								priority: priority.priority,
								firstResponseTime: priority.response_time,
								resolutionTime: priority.resolution_time,
								marker: null // TODO:
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
									from: '',
									to: '' 
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
			} else {
				return {}
			}
		}
	},
	methods: {
		editPolicyName() {
			this.tempSlaPolicyName = this.slaPolicyName
			this.editingName = true
		},
	}
}
</script>

<style>

</style>