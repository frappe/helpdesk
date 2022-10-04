<template>
	<div class="h-full pt-3 space-y-2">
		<div v-for="setting in settings" :key="setting" class="space-y-2">
			<div
				class="cursor-pointer px-3 hover:bg-gray-50 rounded-md mx-2 mb-1"
				:class="selectedSetting === setting.label ? 'bg-gray-50' : ''"
			>
				<router-link :to="{ name: setting.pageName }">
					<div class="p-2 text-base">
						{{ setting.label }}
					</div>
				</router-link>
			</div>
		</div>
	</div>
</template>

<script>
export default {
	name: "SettingsSideBarMenu",
	data() {
		return {
			selectedSetting: "Agents",
			settings: [
				{
					label: "Agents",
					pageName: "Agents",
					route: "/frappedesk/settings/agents",
				},
				{
					label: "Support Policies",
					pageName: "SlaPolicies",
					route: "/frappedesk/settings/sla",
				},
				{
					label: "Email Accounts",
					pageName: "Emails",
					route: "/frappedesk/settings/emails",
				},
			],
		}
	},
	methods: {
		markSettingAsSelected(setting) {
			this.selectedSetting = setting.label
		},
	},
	mounted() {
		this.$event.on("set-selected-setting", (settingLabel) => {
			const setting = this.settings.find((s) => s.label === settingLabel)
			this.markSettingAsSelected(setting)
		})
	},
	unmounted() {
		this.$event.off("set-selected-setting")
	},
}
</script>

<style></style>
