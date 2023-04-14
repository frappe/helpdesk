<template>
	<div class="flex flex-col px-4">
		<ListManager
			ref="agentGroupList"
			:options="{
				cache: ['HD Team', 'Desk'],
				doctype: 'HD Team',
				urlQueryFilters: true,
				saveFiltersLocally: true,
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
						filterBox: true,
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
					class="text-base h-[calc(100vh-9.5rem)] pt-4"
					@add-item="
						() => {
							$router.push('/settings/teams/new')
						}
					"
				>
					<template #field-team_name="{ row }">
						<router-link
							:to="{
								path: `/settings/teams/${row.name}`,
							}"
							class="text-base text-gray-600 font-inter hover:text-gray-900"
						>
							{{ `${row.name}` }}
						</router-link>
					</template>
					<template #field-assignment_rule="{ row }">
						<div class="text-base font-inter text-gray-600">
							{{ row.assignment_rule }}
						</div>
					</template>
					<template #bulk-actions="{ selectedItems }">
						<div class="flex flex-row space-x-2">
							<Button
								@click="
									() => {
										$resources.deleteTeam
											.submit({
												doctype: 'HD Team',
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
				url: "frappe.client.delete",
			}
		},
	},
}
</script>
