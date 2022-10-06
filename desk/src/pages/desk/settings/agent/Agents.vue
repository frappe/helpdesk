<template>
	<div class="mt-[9px]">
		<ListManager
			ref="listManager"
			class="px-[16px]"
			:options="{
				cache: ['Agents', 'Desk'],
				doctype: 'Agent',
				fields: [
					'user as email',
					'user.full_name as full_name',
					'group',
				],
				limit: 20,
			}"
			@selection="
				(selectedItems) => {
					if (Object.keys(selectedItems).length > 0) {
						$event.emit(
							'show-top-panel-actions-settings',
							'Agents Bulk'
						)
					} else {
						$event.emit('show-top-panel-actions-settings', 'Agents')
					}
				}
			"
		>
			<template #body="{ manager }">
				<AgentList :manager="manager" />
			</template>
		</ListManager>
		<AddNewAgentsDialog
			:show="showNewAgentDialog"
			@close="
				() => {
					showNewAgentDialog = false
					$refs.listManager.manager.reload()
					$router.go() // TODO: this is a hack
				}
			"
		/>
	</div>
</template>
<script>
import { inject, ref } from "vue"
import AgentList from "@/components/desk/settings/agents/AgentList.vue"
import ListManager from "@/components/global/ListManager.vue"
import AddNewAgentsDialog from "@/components/desk/global/AddNewAgentsDialog.vue"

export default {
	name: "Agents",
	components: {
		AgentList,
		ListManager,
		AddNewAgentsDialog,
	},
	setup() {
		const viewportWidth = inject("viewportWidth")
		const showNewAgentDialog = ref(false)
		return {
			viewportWidth,
			showNewAgentDialog,
		}
	},
	mounted() {
		this.$event.emit("set-selected-setting", "Agents")
		this.$event.emit("show-top-panel-actions-settings", "Agents")

		this.$event.on("show-new-agent-dialog", () => {
			this.showNewAgentDialog = true
		})
		this.$event.on("delete-selected-agents", () => {
			this.$resources.bulk_delete_agents.submit({
				items: Object.keys(
					this.$refs.listManager.manager.selectedItems
				),
				doctype: "Agent",
			})
		})
	},
	unmounted() {
		this.$event.off("show-new-agent-dialog")
		this.$event.off("delete-selected-agents")
	},
	resources: {
		bulk_delete_agents() {
			return {
				method: "frappedesk.api.doc.delete_items",
				onSuccess: () => {
					this.$router.go()
					// this.$refs.listManager.manager.reload()
					// this.$toast({
					// 	title: 'Agents deleted',
					// 	customIcon: 'circle-check',
					// 	appearance: 'success'
					// })
					// this.$event.emit('show-top-panel-actions-settings', 'Agents')
				},
				onError: (err) => {
					this.$refs.listManager.manager.reload()
					this.$toast({
						title: "Error while deleting agents",
						text: err,
						customIcon: "circle-check",
						appearance: "success",
					})
					this.$event.emit(
						"show-top-panel-actions-settings",
						"Agents"
					)
				},
			}
		},
	},
}
</script>
