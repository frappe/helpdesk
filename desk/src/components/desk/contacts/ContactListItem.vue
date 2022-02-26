<template>
	<div class="block py-4 hover:bg-gray-50 border-b text-base">
		<router-link 
			v-if="contact"
			class="group flex items-center justify-between sm:justify-start font-light pl-4 pr-8"
			:to="`/contacts/${contact.name}`"
		>
			<div
				class="mr-4"
			>
				<Input type="checkbox" value="" />
			</div>
			<div class="sm:w-4/12">
				{{ fullName }}
			</div>
			<div class="sm:w-4/12">
				<div v-if="contact.email_ids.length > 0">
					{{ contact.email_ids[0].email_id }}
				</div>
			</div>
			<div class="sm:w-4/12">
				<div v-if="contact.phone_nos.length > 0">
					{{ contact.phone_nos[0].phone }}
				</div>
			</div>
		</router-link>
	</div>
</template>

<script>
import { Input, FeatherIcon } from 'frappe-ui'

export default {
	name: 'ContactListItem',
	props: ['contactId'],
	components: {
		Input,
		FeatherIcon,
	},
	resources: {
		contact() {
			return {
				method: 'frappe.client.get',
				params: {
					doctype: "Contact",
					name: this.contactId
				},
				auto: true,
			}
		}
	},
	computed: {
		contact() {
			return this.$resources.contact.data || null
		},
		fullName() {
			if (this.contact) {
				return (this.contact.first_name || "") + " " + (this.contact.last_name || "")
			}
		},
	}
}
</script>

<style>

</style>