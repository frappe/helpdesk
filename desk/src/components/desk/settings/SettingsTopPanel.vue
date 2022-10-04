<template>
	<div class="flow-root py-3 pl-5 pr-8 border-b h-[55px]">
		<div class="float-left">
			<div class="flex items-center">
				<div class="font-normal text-2xl">Settings</div>
			</div>
		</div>
		<div class="float-right">
			<div class="flex space-x-3 items-center">
				<div v-for="action in actions" :key="action">
					<Button
						:appearance="action.appearance"
						@click="action.onClick()"
						:icon-left="action.icon"
						>{{ action.label }}</Button
					>
				</div>
			</div>
		</div>
	</div>
</template>

<script>
import { ref } from "vue"

class Action {
	constructor(label, icon, appearance, onClick) {
		this.label = label
		this.icon = icon
		this.appearance = appearance
		this.onClick = onClick
	}
}

export default {
	props: ["selectedSetting"],
	setup() {
		const actions = ref({})

		return {
			actions,
		}
	},
	mounted() {
		this.actionGroups = {
			Agents: [
				new Action("New Agent", "plus", "primary", () => {
					this.$event.emit("show-new-agent-dialog")
				}),
			],
			"Agents Bulk": [
				new Action("Delete", "", "secondary", () => {
					this.$event.emit("delete-selected-agents")
				}),
			],
			"Support Policies": [
				new Action("New Policy", "plus", "primary", () => {
					this.$router.push({ name: "NewSlaPolicy" })
				}),
			],
			"Support Policies Bulk": [],
			"Email Accounts": [
				new Action("New Email", "plus", "primary", () => {
					this.$router.push({ name: "NewEmailAccount" })
				}),
			],
			"Email Accounts Bulk": [],
		}

		this.$event.on("show-top-panel-actions-settings", (group) => {
			this.actions = []
			if (this.actionGroups[group]) {
				this.actions = this.actionGroups[group]
			}
		})
	},
	unmounted() {
		this.$event.off("show-top-panel-actions-settings")
	},
}
</script>

<style></style>
