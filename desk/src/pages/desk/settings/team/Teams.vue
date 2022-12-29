<template>
	<div class="flex flex-col h-full px-4">
		<ListManager
			ref="agentGroupList"
			:options="{
				cache: ['Agent Group', 'Desk'],
				doctype: 'Agent Group',
				fields: ['team_name', 'assignment_rule'],
				limit: 20,
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
							showAddNewTeamDialog = true
						}
					"
				>
					<template #field-team_name="{ row }">
						<router-link
							:to="{
								path: `/frappedesk/settings/team/${row.name}`,
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
		<AddNewTeamDialog
			v-model="showAddNewTeamDialog"
			@close="
				() => {
					showAddNewTeamDialog = false
				}
			"
		/>
	</div>
</template>

<script>
import ListManager from "@/components/global/ListManager.vue"
import ListViewer from "@/components/global/ListViewer.vue"
import AddNewTeamDialog from "@/components/desk/global/AddNewTeamDialog.vue"
export default {
	name: "Teams",
	components: {
		ListManager,
		ListViewer,
		AddNewTeamDialog,
	},
	data() {
		return {
			showAddNewTeamDialog: false,
		}
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
