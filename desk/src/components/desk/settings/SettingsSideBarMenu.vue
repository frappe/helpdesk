<template>
	<div class="h-full pt-1 space-y-2">
		<div v-for="setting in settings" :key="setting" class="space-y-2">
			<div class="cursor-pointer px-3 hover:bg-slate-50 rounded-md mx-2 mb-1" :class="selectedSetting === setting.label ? 'bg-slate-50' : ''">
				<div @click="changeSelectedSettingItem(setting)">
					<ListItem  :title="setting.label" />
				</div>
			</div>
		</div>
	</div>
</template>

<script>
import { ListItem } from 'frappe-ui'
import { inject } from 'vue'

export default {
	name: 'SettingsSideBarMenu',
	components: {
		ListItem
	},
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
					route: '/helpdesk/settings/agents'
				},
				{
					label: 'Support Policies',
					pageName: 'SlaPolicies',
					route: '/helpdesk/settings/sla'
				}
			]
		}
	},
	methods: {
		changeSelectedSettingItem(setting) {
			this.selectedSetting = setting.label
			this.$router.push({
				name: setting.pageName,
			})
		}
	}
}
</script>

<style>

</style>