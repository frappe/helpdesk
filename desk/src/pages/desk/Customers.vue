<template>
	<div class="flex flex-col h-full px-4">
		<ListManager
			ref="fdCustomerList"
			:options="{
				cache: ['FD Customer', 'Desk'],
				doctype: 'FD Customer',
				fields: ['customer_name', 'domain'],
				limit: 20,
			}"
		>
			<template #body>
				<ListViewer
					:options="{
						base: '12',
						filterBox: true,
						presetFilters: true,
						fields: {
							customer_name: {
								label: 'Name',
								width: '4',
							},
							contact: {
								label: 'Contacts',
								width: '4',
							},
						},
					}"
					class="text-base h-[100vh] pt-4"
					@add-item="
						() => {
							showNewCustomerDialog = true
						}
					"
				>
					<template #field-customer_name="{ row }">
						<router-link
							:to="{ path: `/frappedesk/customers/${row.name}` }"
						>
							{{ `${row.customer_name}` }}
						</router-link>
					</template>
				</ListViewer>
			</template>
		</ListManager>
		<NewCustomerDialog
			v-model="showNewCustomerDialog"
			@close="
				() => {
					showNewCustomerDialog = false
				}
			"
		/>
	</div>
</template>
<script>
import ListManager from "@/components/global/ListManager.vue"
import ListViewer from "@/components/global/ListViewer.vue"
import NewCustomerDialog from "@/components/desk/global/NewCustomerDialog.vue"
export default {
	name: "Customers",
	components: {
		ListManager,
		ListViewer,
		NewCustomerDialog,
	},
	data() {
		return {
			showNewCustomerDialog: false,
		}
	},
}
</script>
