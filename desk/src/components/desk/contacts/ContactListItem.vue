<template>
	<div class="block hover:bg-gray-50 border-b text-base">
		<router-link 
			v-if="contact"
			class="group flex items-center justify-between sm:justify-start font-light h-10"
			:to="`/helpdesk/contacts/${contact.name}`"
		>
			<div class="mr-2">
				<Input type="checkbox" value="" />
			</div>
			<div class="sm:w-3/12 truncate pr-10">
				{{ fullName }}
			</div>
			<div class="sm:w-3/12 truncate pr-10">
				<div v-if="contact.email_ids && contact.email_ids.length > 0">
					{{ contact.email_ids[0].email_id }}
				</div>
				<div v-else-if="contact.email_id">
					{{ contact.email_id }}
				</div>
			</div>
			<div class="sm:w-3/12 truncate pr-10">
				<div v-if="contact.phone_nos && contact.phone_nos.length > 0">
					{{ contact.phone_nos[0].phone }}
				</div>
				<div v-if="contact.phone">
					{{ contact.phone }}
				</div>
			</div>
			<div class="sm:w-3/12 truncate pr-10">Temp Org</div>
		</router-link>
	</div>
</template>

<script>
import { Input, FeatherIcon } from 'frappe-ui'

export default {
	name: 'ContactListItem',
	props: ['contact'],
	components: {
		Input,
		FeatherIcon,
	},
	computed: {
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