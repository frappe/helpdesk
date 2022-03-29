<template>
	<div>
		<div class="flow-root pt-3 pb-5 pr-8 pl-4">
			<div class="float-left">
				<div class="flex items-center">
					<div class="font-semibold text-xl">Contacts</div>
				</div>
			</div>
			<div class="float-right">
				<div class="flex items-center space-x-4">
					<Button icon-left="plus" appearance="primary" @click="() => {showNewContactDialog = true}">Add Contact</Button>
				</div>
			</div>
		</div>
		<div v-if="contacts">
			<ContactList />
		</div>
		<NewContactDialog v-model="showNewContactDialog" @contact-created="() => {showNewContactDialog = false}" />
	</div>
</template>
<script>
import { Input } from 'frappe-ui'
import ContactList from '@/components/desk/contacts/ContactList.vue'
import NewContactDialog from '@/components/desk/global/NewContactDialog.vue'
import { inject, ref } from '@vue/runtime-core'

export default {
	name: 'Contacts',
	components: {
		ContactList,
		Input,
		NewContactDialog
	},
	setup() {
		const showNewContactDialog = ref(false)
		const viewportWidth = inject('viewportWidth')
		const contacts = inject('contacts')

		return { showNewContactDialog, viewportWidth, contacts}
	},
	computed: {
		contacts() {
			return this.contacts || null
		}
	},
    activated() {
    },
    deactivated() {

    },
	updated() {
		this.$currentPage.set('Contacts', [])
	},
}
</script>
