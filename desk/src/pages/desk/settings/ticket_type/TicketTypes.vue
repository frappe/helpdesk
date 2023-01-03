<template>
	<div class="flex flex-col h-full px-4">
		<ListManager
			ref="ticketTypeList"
			:options="{
				cache: ['Ticket Type', 'Desk'],
				doctype: 'Ticket Type',
				fields: ['name', 'priority'],
				limit: 20,
				order_by: 'modified desc',
			}"
		>
			<template #body="{ manager }">
				<ListViewer
					:options="{
						base: '12',
						presetFilters: true,
						fields: {
							name: {
								label: 'Name',
								width: '4',
							},
							priority: {
								label: 'Priority',
								width: '2',
							},
						},
					}"
					class="text-base h-[100vh] pt-4"
					@add-item="
						$router.push('/frappedesk/settings/ticket_types/new')
					"
				>
					<template #field-name="{ row }">
						<router-link
							:to="{
								path: `/frappedesk/settings/ticket_types/${row.name}`,
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
										$resources.deleteTicketType
											.submit({
												doctype: 'Ticket Type',
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
	name: "TicketTypes",
	components: {
		ListManager,
		ListViewer,
	},
	setup() {},
	mounted() {
		this.$event.emit("set-selected-setting", "Ticket Types")
	},

	resources: {
		deleteTicketType() {
			return {
				method: "frappe.client.delete",
			}
		},
	},
}
</script>
