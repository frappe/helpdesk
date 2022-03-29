<template>
	<div>
		<div>
			<div
				v-if="contacts"
				class="w-full pl-4 pr-8"
			>
				<div class="border-b pb-3 group flex items-center font-light text-base text-slate-500">
					<div class="mr-2">
						<Input type="checkbox" value="" />
					</div>
					<div class="w-3/12">Name</div>
					<div class="w-3/12">Email</div>
					<div class="w-3/12">Phone</div>
					<div class="w-3/12">Organization</div>
				</div>
				<div 
					class="block overflow-auto"
					:style="{ height: viewportWidth > 768 ? 'calc(100vh - 9.4rem)' : null }"
				>
					<div v-for="contact in contacts" :key="contact.name">
						<div>
							<ContactListItem :contact="contact" />
						</div>
					</div>
				</div>
			</div>
		</div>
	</div>
</template>

<script>
import { Input } from 'frappe-ui'
import ContactListItem from './ContactListItem.vue'
import { inject } from '@vue/runtime-core'

export default {
	name: 'ContactList',
	components: {
		Input,
		ContactListItem
	},
	setup() {
		const viewportWidth = inject('viewportWidth')
		const contacts = inject('contacts')

		return { viewportWidth, contacts }
	},
	computed: {
		contacts() {
			return this.contacts || null
		}
	}
}
</script>
