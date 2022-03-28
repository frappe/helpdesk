<template>
	<div>
		<div class="flow-root border-b pt-2 pb-3 pr-8">
			<div class="float-left ml-4">
				<div class="flex items-center space-x-4">
					<Input type="checkbox" value="" />
					<Button icon-left="plus" appearance="primary" @click="() => {showNewContactDialog = true}">Add Contact</Button>
				</div>
			</div>
			<div class="float-right">
				<Button icon-left="filter" type="white">Filter</Button>
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
}
</script>
