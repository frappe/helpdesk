<template>
	<div class="flex flex-col h-full px-4">
		<ListManager
			ref="agentGroupList"
			:options="{
				cache: ['Agent Group', 'Desk'],
				doctype: 'Agent Group',
				fields: ['team_name', 'assignment_rule'],
				limit: 20,
				order_by: 'modified desc',
			}"
		>
			<template #body="{ manager }">
				<ListViewer
					:options="{
						name: 'Teams',
						base: '12',
						listTitle: 'Teams',
						presetFilters: true,
						fields: {
							team_name: {
								label: 'Name',
								width: '4',
							},
							assignment_rule: {
								label: 'Assignment Rule',
								width: '2',
							},
						},
					}"
					class="text-base h-[100vh] pt-4"
					@add-item="
						() => {
							$router.push('/frappedesk/settings/teams/new')
						}
					"
				>
					<template #field-team_name="{ row }">
						<router-link
							:to="{
								path: `/frappedesk/settings/teams/${row.name}`,
							}"
						>
							{{ `${row.name}` }}
						</router-link>
					</template>
					<template #bulk-actions="{ selectedItems }">
						<div class="flex flex-row space-x-2">
							<Button
								@click="
									() => {
										$resources.deleteTeam
											.submit({
												doctype: 'Agent Group',
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
	</div>
</template>

<script>
import ListManager from "@/components/global/ListManager.vue"
import ListViewer from "@/components/global/ListViewer.vue"
export default {
	name: "Teams",
	components: {
		ListManager,
		ListViewer,
	},
	setup() {},
	mounted() {
		this.$event.emit("set-selected-setting", "Teams")
	},
	resources: {
		deleteTeam() {
			return {
				method: "frappe.client.delete",
			}
		},
	},
}
</script>
