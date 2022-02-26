<template>
	<div>
		<div>
			<div
				v-if="contacts"
				class="w-full block overflow-auto"
				:style="{ height: viewportWidth > 768 ? 'calc(100vh - 7.3rem)' : null }"
			>
				<div class="flex-auto" v-for="contact in contacts" :key="contact.name">
					<div class="block px-0">
						<ContactListItem :contactId="contact.name" />
					</div>
				</div>
			</div>
		</div>
	</div>
</template>

<script>
import { Input } from 'frappe-ui'
import ContactListItem from './ContactListItem.vue'

export default {
	name: 'ContactList',
	inject: ['viewportWidth'],
	props: ['contacts'],
	components: {
		Input,
		ContactListItem
	},
}
</script>
