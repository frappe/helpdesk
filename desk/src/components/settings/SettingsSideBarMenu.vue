<template>
	<div class="border-r h-full pt-1 space-y-2">
		<div class="border-b pb-3 px-3 mx-2">Settings</div>
		<div v-for="setting in settings" :key="setting" class="space-y-2">
			<div class="cursor-pointer px-3 hover:bg-slate-50 rounded-md mx-2 mb-1">
				<router-link 
					:to="setting.route"
				>
					<ListItem  :title="setting.label" />
				</router-link>
			</div>
		</div>
	</div>
</template>

<script>
import { ListItem } from 'frappe-ui'

export default {
	name: 'SettingsSideBarMenu',
	components: {
		ListItem
	},
	data() {
		return {
			settings: [
				{
					label: 'Agents',
					route: '/settings/agents'
				},
				{
					label: 'SLA Policies',
					route: '/settings/sla'
				}
			]
		}
	}
}
</script>

<style>

</style>