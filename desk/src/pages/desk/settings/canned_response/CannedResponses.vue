<template>
	<div class="flex flex-col px-4">
		<ListManager
			ref="listManager"
			:options="{
				doctype: 'Canned Response',
				urlQueryFilters: true,
				saveFiltersLocally: true,
				fields: ['title', 'owner'],
				limit: 20,
				order_by: 'modified desc',
			}"
		>
			<template #body="{ manager }">
				<ListViewer
					:options="{
						name: 'Response',
						base: '12',
						listTitle: 'Canned Responses',
						filterBox: true,
						presetFilters: true,
						fields: {
							title: {
								label: 'Title',
								width: '4',
							},
							owner: {
								label: 'Owner',
								width: '2',
							},
						},
					}"
					class="text-base h-[calc(100vh-9.5rem)] pt-4"
					@add-item="
						() => {
							showNewCannedResponsesDialog = true
						}
					"
				>
					<template #field-title="{ row }">
						<router-link
							:to="{
								path: `/frappedesk/settings/canned_responses/${row.title}`,
							}"
							class="text-[13px] text-gray-600 font-inter hover:text-gray-900"
						>
							{{ `${row.title}` }}
						</router-link>
					</template>
					<template #field-owner="{ row }">
						<div class="text-[13px] font-inter text-gray-600">
							{{ row.owner }}
						</div>
					</template>
					<template #bulk-actions="{ selectedItems }">
						<div class="flex flex-row space-x-2">
							<Button
								@click="
									() => {
										$resources.deleteTeam
											.submit({
												doctype: 'Canned Response',
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
		<AddNewCannedResponsesDialog
			:show="showNewCannedResponsesDialog"
			@close="
				() => {
					showNewCannedResponsesDialog = false
					$refs.listManager.manager.reload()
					$router.go()
				}
			"
		/>
	</div>
</template>
<script>
import { inject, ref } from "vue"
import ListManager from "@/components/global/ListManager.vue"
import AddNewCannedResponsesDialog from "@/components/desk/global/AddNewCannedResponsesDialog.vue"
import ListViewer from "@/components/global/ListViewer.vue"
export default {
	name: "Canned Responses",
	components: {
		ListManager,
		AddNewCannedResponsesDialog,
		ListViewer,
	},
	setup() {
		const viewportWidth = inject("viewportWidth")
		const showNewCannedResponsesDialog = ref(false)
		return {
			viewportWidth,
			showNewCannedResponsesDialog,
		}
	},

	resources: {
		deleteTeam() {
			return {
				method: "frappe.client.delete",
			}
		},
		bulk_delete_responses() {
			return {
				method: "frappedesk.api.doc.delete_items",
				onSuccess: () => {
					this.$router.go()
				},
				onError: (err) => {
					this.$refs.listManager.manager.reload()
					this.$toast({
						title: "Error while deleting canned responses",
						text: err,
						customIcon: "circle-check",
						appearance: "success",
					})
				},
			}
		},
	},
}
</script>
