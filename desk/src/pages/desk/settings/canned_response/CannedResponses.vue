<template>
	<div class="mt-[9px]">
		<ListManager
			ref="listManager"
			class="px-[16px]"
			:options="{
				doctype: 'Canned Response',
				fields: ['title','owner'],
				limit: 20,
			}"
			@selection="
				(selectedItems) => {
					if (Object.keys(selectedItems).length > 0) {
						$event.emit(
							'show-top-panel-actions-settings',
							'Canned Responses Bulk'
						)
					} else {
						$event.emit('show-top-panel-actions-settings', 'CannedResponses')
					}
				}
			"
		>
			<template #body="{ manager }">
				<CannedResponseList :manager="manager" />
			</template>
		</ListManager>
	</div>
</template>
<script>
import { inject, ref } from "vue"
import CannedResponseList from "@/components/desk/settings/canned_responses/CannedResponseList.vue"
import ListManager from "@/components/global/ListManager.vue"

export default {
	name: "Canned Responses",
	components: {
    CannedResponseList,
    ListManager,
},
	setup() {
		const viewportWidth = inject("viewportWidth")
		const showNewCannedResponsesDialog = ref(false)
		return {
			viewportWidth,
			showNewCannedResponsesDialog,
		}
	},
	mounted() {
		// this.$event.emit("set-selected-setting", "CannedResponses")
		this.$event.emit("show-top-panel-actions-settings", "CannedResponses")
		this.$event.on("delete-selected-canned_responses", () => {
			this.$resources.bulk_delete_responses.submit({
				items: Object.keys(
					this.$refs.listManager.manager.selectedItems
				),
				doctype: "Canned Response",
			})
		})
	},
	unmounted() {

		this.$event.off("delete-selected-canned_responses")
	},
	resources: {
		bulk_delete_responses() {
			return {
				method: "frappedesk.api.doc.delete_items",
				onSuccess: () => {
					this.$router.go()
					// this.$refs.listManager.manager.reload()
					// this.$toast({
					// 	title: 'Canned Responses deleted',
					// 	customIcon: 'circle-check',
					// 	appearance: 'success'
					// })
					// this.$event.emit('show-top-panel-actions-settings', 'CannedResponses')
				},
				onError: (err) => {
					this.$refs.listManager.manager.reload()
					this.$toast({
						title: "Error while deleting canned responses",
						text: err,
						customIcon: "circle-check",
						appearance: "success",
					})
					this.$event.emit(
						"show-top-panel-actions-settings",
						"CannedResponses"
					)
				},
			}
		},
	},
}
</script>