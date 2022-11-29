<template>
	<div class="flex flex-col h-full px-4">
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
				],
				limit: 20,
			}"
		>
			<template #body="{ manager }">
				<ListViewer
					:options="{
						base: '12',
						fields: {
							first_name: {
								label: 'Name',
								width: '4',
							},
							email: {
								label: 'Email',
								width: '4',
							},
							phone: {
								label: 'Phone',
								width: '4',
							},
						},
					}"
					class="text-base h-[100vh] pt-4"
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
							{{ `${row.first_name} ${row.last_name}` }}
						</router-link>
					</template>
					<template #bulk-actions="{ selectedItems }">
						<div class="flex flex-row space-x-2">
							<!-- <Button @click="() => {}">Add to FAQ</Button> -->
							<Button
								appearance="danger"
								@click="
									() => {
										$resources.deleteContact
											.submit({
												items: Object.keys(
													selectedItems
												),
												doctype: 'Contact',
											})
											.then(() => {
												manager.unselect()
												manager.reload()
											})
									}
								"
							>
								Delete
							</Button>
						</div>
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
	resources: {
		deleteContact() {
			return {
				// method: "frappedesk.api.delete_contact.delete_bulk_contact",
				method: "frappedesk.api.doc.delete_items",
				onSuccess: () => {
					this.$toast({
						title: "Contact Deleted.",
						customIcon: "circle-check",
						appearance: "success",
					})
					// this.$router.go()
					// this.ListManager.reload()
					// this.ListViewer.reload()
				},
				onError: (err) => {
					this.$toast({
						title: "Error while deleting contacts",
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
