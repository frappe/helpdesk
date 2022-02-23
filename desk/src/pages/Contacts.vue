<template>
	<div>
		<div class="flow-root border-b pt-2 pb-3 pr-8">
			<div class="float-left ml-4">
				<div class="flex items-center space-x-4">
					<Input type="checkbox" value="" />
					<Button icon-left="plus" appearance="primary" @click="() => {showNewTicketDialog = true}">Add Contact</Button>
				</div>
			</div>
			<div class="float-right">
				<Button icon-left="filter" type="white">Filter</Button>
			</div>
		</div>
		<div v-if="contacts">
			<ContactList :contacts="contacts" />
		</div>
	</div>
</template>
<script>
import { Input } from 'frappe-ui'
import ContactList from '../components/contacts/ContactList.vue'
import NewTicketDialog from '../components/tickets/NewTicketDialog.vue'

export default {
	name: 'Contacts',
	inject: ['viewportWidth'],
	components: {
		ContactList,
		Input,
		NewTicketDialog
	},
	data() {
		return {
			showNewTicketDialog: false
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
    }
}
</script>
