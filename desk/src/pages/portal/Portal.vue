<template>
	<div v-if="user.isLoggedIn()">
		<router-view v-slot="{ Component }">
			<component :is="Component" />
		</router-view>
	</div>
</template>

<script>
import { inject, provide, ref } from 'vue'

export default {
	name: "App",
	setup() {
		const user = inject('user')

		const tickets = ref()
		const ticketController = ref({})

		provide('tickets', tickets)
		provide('ticketController', ticketController)

		return { user, tickets, ticketController }
	},
	mounted() {
		this.ticketController.createTicket = ((template='Default') => {
			console.log('create ticket')
		})
		this.ticketController.set = ((ticketId, type, ref) => {

		})
	},
	resources: {
		tickets() {
			return {
				method: 'helpdesk.helpdesk.doctype.ticket.ticket.get_user_tickets',
				auto: true,
				onSuccess: (data) => {
					this.tickets = {}
					for (var i = 0; i < data.length; i++) {
						this.tickets[data[i].name] = data[i]
					}
				},
				onFailure: () => {
					console.log('error occured!!')
				}
			}
		}
	}
}
</script>