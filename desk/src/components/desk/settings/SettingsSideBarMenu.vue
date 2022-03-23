<template>
	<div class="h-full pt-1 space-y-2">
		<div v-for="setting in settings" :key="setting" class="space-y-2">
			<div class="cursor-pointer px-3 hover:bg-slate-50 rounded-md mx-2 mb-1" :class="$currentPage.get() == setting.pageName ? 'bg-slate-50' : ''">
				<div @click="changeSelectedSettingItem(setting)">
					<ListItem  :title="setting.label" />
				</div>
			</div>
		</div>
	</div>
</template>

<script>
import { ListItem } from 'frappe-ui'

export default {
	name: 'SettingsSideBarMenu',
	props: ['modelValue'],
	components: {
		ListItem
	},
	data() {
		return {
			settings: [
				{
					label: 'Agents',
					pageName: 'AgentSettings',
					route: '/helpdesk/settings/agents'
				},
				{
					label: 'SLA Policies',
					pageName: 'SlaSettings',
					route: '/helpdesk/settings/sla'
				}
			]
		}
	},
	methods: {
		changeSelectedSettingItem(setting) {
			this.$emit('update:modelValue', setting.label)
			this.$router.push({
				name: setting.pageName,
			})
		}
	}
}
</script>

<style>

</style>