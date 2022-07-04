<template>
	<div class="h-full pt-1 space-y-2">
		<div v-for="setting in settings" :key="setting" class="space-y-2">
			<div class="cursor-pointer px-3 hover:bg-slate-50 rounded-md mx-2 mb-1" :class="selectedSetting === setting.label ? 'bg-slate-50' : ''">
				<div class="p-2 text-base" @click="changeSelectedSettingItem(setting)">
					{{ setting.label }}
				</div>
			</div>
		</div>
	</div>
</template>

<script>
import { inject } from 'vue'

export default {
	name: 'SettingsSideBarMenu',
	setup() {
		const selectedSetting = inject('selectedSetting')

		return { selectedSetting }
	},
	data() {
		return {
			settings: [
				{
					label: 'Agents',
					pageName: 'Agents',
					route: '/frappedesk/settings/agents'
				},
				{
					label: 'Support Policies',
					pageName: 'SlaPolicies',
					route: '/frappedesk/settings/sla'
				},
				{
					label: 'Email Accounts',
					pageName: 'Emails',
					route: '/frappedesk/settings/emails'
				},
				{
					label: 'Helpdesk Settings',
					pageName: 'Helpdesk Settings',
					route: '/frappedesk/settings/helpdesk'
				}
			]
		}
	},
	methods: {
		changeSelectedSettingItem(setting) {
			this.selectedSetting = setting.label
			if (setting.pageName) {
				this.$router.push({
					name: setting.pageName,
				})
			} else if (setting.action) {
				setting.action()
			}
		}
	}
}
</script>

<style>

</style>