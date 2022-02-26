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
			<ContactList :contacts="contacts" />
		</div>
		<NewContactDialog v-model="showNewContactDialog" @contact-created="(contact) => {contactCreated(contact)}"/>
	</div>
</template>
<script>
import { Input } from 'frappe-ui'
import ContactList from '@/components/desk/contacts/ContactList.vue'
import NewContactDialog from '@/components/desk/global/NewContactDialog.vue'

export default {
	name: 'Contacts',
	inject: ['viewportWidth'],
	components: {
		ContactList,
		Input,
		NewContactDialog
	},
	data() {
		return {
			showNewContactDialog: false
		}
	},
    resources: {
        contacts() {
            return {
                method: 'helpdesk.api.contact.get_all',
                auto: true,
                fields: ['name']
            }
        }
    },
    activated() {
        this.$currentPage.set('Contacts')
    },
    deactivated() {

    },
    computed: {
        contacts() {
            return this.$resources.contacts.data || null
        }
    },
	methods: {
		contactCreated(contact) {
			this.$resources.contacts.fetch();
			this.showNewContactDialog = false
		}
	}
}
</script>
