<template>
	<div class="mt-[9px]">
		<ListManager
			class="px-[16px]"
			:options="{
				cache: ['SLA', 'Settings'],
				doctype: 'SLA',
				fields: ['name', 'default_sla', 'enabled'],
				limit: 20,
			}"
		>
			<template #body="{ manager }">
				<SlaPolicyList :manager="manager" />
			</template>
		</ListManager>
	</div>
</template>
<script>
import { inject } from "vue"
import ListManager from "@/components/global/ListManager.vue"
import SlaPolicyList from "@/components/desk/settings/policies/SlaPolicyList.vue"

export default {
	name: "SlaPolicies",
	components: {
		SlaPolicyList,
		ListManager,
	},
	setup() {
		const viewportWidth = inject("viewportWidth")

		return {
			viewportWidth,
		}
	},
	mounted() {
		this.$event.emit("set-selected-setting", "Support Policies")
		this.$event.emit("show-top-panel-actions-settings", "Support Policies")
	},
}
</script>
