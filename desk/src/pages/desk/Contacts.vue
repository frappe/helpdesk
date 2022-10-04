<template>
	<div>
		<div>
			<ListManager
				class="px-[16px]"
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
					group: ['email', 'phone'],
					limit: 40,
					start_page: initialPage,
					route_query_pagination: true,
				}"
			>
				<template #body="{ manager }">
					<div>
						<div class="flow-root py-4 px-[16px]">
							<div class="float-left"></div>
							<div class="float-right">
								<div class="flex items-center space-x-3">
									<div
										class="stroke-blue-500 fill-blue-500 w-0 h-0 block"
									></div>
									<Button
										icon-left="plus"
										appearance="primary"
										@click="
											() => {
												showNewContactDialog = true
											}
										"
										>Add Contact</Button
									>
								</div>
							</div>
						</div>
						<ContactList :manager="manager" />
					</div>
				</template>
			</ListManager>
		</div>
		<NewContactDialog
			v-model="showNewContactDialog"
			@contact-created="
				() => {
					showNewContactDialog = false
				}
			"
		/>
	</div>
</template>
<script>
import ListManager from "@/components/global/ListManager.vue"
import ContactList from "../../components/desk/contacts/ContactList.vue"
import NewContactDialog from "@/components/desk/global/NewContactDialog.vue"
import { ref } from "vue"

export default {
	name: "Contacts",
	components: {
		ListManager,
		NewContactDialog,
		ContactList,
	},
	data() {
		return {
			initialPage: 1,
		}
	},
	setup() {
		const showNewContactDialog = ref(false)

		return {
			showNewContactDialog,
		}
	},
	computed: {
		contacts() {
			return this.contacts || null
		},
	},
	mounted() {
		this.initialPage = parseInt(
			this.$route.query.page ? this.$route.query.page : 1
		)
	},
}
</script>
