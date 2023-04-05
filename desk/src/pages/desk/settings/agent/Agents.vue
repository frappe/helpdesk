<template>
	<div class="flex flex-col px-4">
		<ListManager
			ref="listManager"
			:options="{
				cache: ['Agents', 'Desk'],
				doctype: 'HD Agent',
				urlQueryFilters: true,
				saveFiltersLocally: true,
				fields: ['user', 'agent_name'],
				limit: 20,
			}"
		>
			<template #body="{ manager }">
				<ListViewer
					:options="{
						name: 'Agent',
						base: '12',
						listTitle: 'Agents',
						filterBox: true,
						presetFilters: true,
						fields: {
							agent_name: { label: 'Name', width: '4' },
							user: {
								label: 'Email',
								width: '2',
							},
						},
					}"
					class="text-base h-[calc(100vh-9.5rem)] pt-4"
					@add-item="
						() => {
							showNewAgentDialog = true
						}
					"
				>
					<template #field-agent_name="{ row }">
						<router-link
							:to="{
								path: `/settings/agents/${row.user}`,
							}"
							class="text-[13px] text-gray-600 font-inter hover:text-gray-900"
						>
							{{ `${row.agent_name}` }}
						</router-link>
					</template>
					<template #field-user="{ row }">
						<div class="text-[13px] font-inter text-gray-600">
							{{ `${row.user}` }}
						</div>
					</template>
					<template #bulk-actions="{ selectedItems }">
						<div class="flex flex-row space-x-2">
							<Button
								@click="
									() => {
										$resources.deleteAgent
											.submit({
												doctype: 'HD Agent',
												name: Object.keys(
													selectedItems
												),
											})
											.then(() => {
												manager.unselect()
												manager.reload()
											})
									}
								"
								>Delete</Button
							>
						</div>
					</template>
				</ListViewer>
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
import ListViewer from "@/components/global/ListViewer.vue"
export default {
	name: "Agents",
	components: {
		AgentList,
		ListManager,
		AddNewAgentsDialog,
		ListViewer,
	},
	setup() {
		const viewportWidth = inject("viewportWidth")
		const showNewAgentDialog = ref(false)
		return {
			viewportWidth,
			showNewAgentDialog,
		}
	},

	resources: {
		deleteAgent() {
			return {
				url: "frappe.client.delete",
			}
		},
		bulk_delete_agents() {
			return {
				url: "helpdesk.api.doc.delete_items",
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
						icon: "check",
						iconClasses: "text-red-500",
					})
				},
			}
		},
	},
}
</script>
