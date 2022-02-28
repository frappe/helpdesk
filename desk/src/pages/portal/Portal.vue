<template>
	<div>
		<div v-if="user.isLoggedIn()">
			<router-view v-slot="{ Component }">
				<component :is="Component" />
			</router-view>
		</div>
		<div v-else>
			<div class="mx-auto max-w-3xl mt-20">
				<div class="p-6 bg-orange-50 border rounded-lg shadow space-y-4">
					<p class="font-bold text-amber-700">Please login to be able to create tickets</p>
					<p class="text-amber-700">If you don't already have an account, you can sign up for a new account.</p>
					<Button appearance="primary" @click="user.showLoginPage()">Login to continue</Button>
				</div>
			</div>
		</div>
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