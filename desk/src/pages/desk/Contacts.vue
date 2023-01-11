<template>
	<div class="flex flex-col px-4">
		<ListManager
			ref="contactList"
			:options="{
				cache: ['Contacts', 'Desk'],
				doctype: 'Contact',
				fields: [
					'first_name',
					'last_name',
					'email_ids.email_id as email',
					'phone_nos.phone as phone',
					'links.link_name as customer',
				],
				limit: 20,
			}"
		>
			<template #body>
				<ListViewer
					:options="{
						base: '12',
						presetFilters: true,
						fields: {
							first_name: {
								label: 'Name',
								width: '3',
							},
							email: {
								label: 'Email',
								width: '3',
							},
							phone: {
								label: 'Phone',
								width: '3',
							},
							customer: {
								label: 'Customer',
								width: '3',
							},
						},
					}"
					class="text-base h-[calc(100vh-5.5rem)] pt-4"
					@add-item="
						() => {
							showNewContactDialog = true
						}
					"
				>
					<template #field-first_name="{ row }">
						<router-link
							:to="{ path: `/frappedesk/contacts/${row.name}` }"
						>
							{{ row.first_name || "" }} {{ row.last_name || "" }}
						</router-link>
					</template>
				</ListViewer>
			</template>
		</ListManager>
		<NewContactDialog
			v-model="showNewContactDialog"
			@contact-created="
				() => {
					showNewContactDialog = false
					$refs.contactList.manager.reload()
				}
			"
		/>
	</div>
</template>
<script>
import ListManager from "@/components/global/ListManager.vue"
import ListViewer from "@/components/global/ListViewer.vue"
import NewContactDialog from "@/components/desk/global/NewContactDialog.vue"

export default {
	name: "Contacts",
	components: {
		ListManager,
		ListViewer,
		NewContactDialog,
	},
	data() {
		return {
			showNewContactDialog: false,
		}
	},
}
</script>
