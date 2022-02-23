<template>
	<div>
		<div>
			<div
				v-if="this.tickets"
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
	computed: {
		tickets() {
			let tickets = this.$tickets().get()
			let filter = this.$ticketFilter.get()

			let filteredTickets = []

			if (filter == "Assigned to me") {
				for (let i in tickets) {
					if (tickets[i].assignees.length > 0) {
						for (let j = 0; j < tickets[i].assignees.length; j++) {
							if (tickets[i].assignees[j].name == this.$user.get().agent.name) {
								filteredTickets.push(tickets[i])
							}
						}
					}
				}
			} else {
				filteredTickets = tickets
			}

			return filteredTickets;
		}
	}
}
</script>
