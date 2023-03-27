<template>
	<div class="flex flex-col px-4">
		<ListManager
			ref="ticketTypeList"
			:options="{
				cache: ['HD Ticket Type', 'Desk'],
				doctype: 'HD Ticket Type',
				urlQueryFilters: true,
				saveFiltersLocally: true,
				fields: ['name', 'priority'],
				limit: 20,
				order_by: 'modified desc',
			}"
		>
			<template #body="{ manager }">
				<ListViewer
					:options="{
						base: '12',
						filterBox: true,
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
					class="text-base h-[calc(100vh-9.5rem)] pt-4"
					@add-item="
						$router.push('/frappedesk/settings/ticket_types/new')
					"
				>
					<template #field-name="{ row }">
						<router-link
							:to="{
								path: `/frappedesk/settings/ticket_types/${row.name}`,
							}"
							class="text-[13px] text-gray-600 font-inter hover:text-gray-900"
						>
							{{ `${row.name}` }}
						</router-link>
					</template>
					<template #field-priority="{ row }">
						<div class="text-[13px] font-inter text-gray-600">
							{{ row.priority }}
						</div>
					</template>
					<template #bulk-actions="{ selectedItems }">
						<div class="flex flex-row space-x-2">
							<Button
								@click="
									() => {
										$resources.deleteTicketType
											.submit({
												doctype: 'HD Ticket Type',
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
				url: "frappe.client.delete",
			}
		},
	},
}
</script>
