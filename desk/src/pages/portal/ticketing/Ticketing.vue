<template>
	<div v-if="authStore.isLoggedIn">
		<router-view v-slot="{ Component }" :key="$route.fullPath">
			<component :is="Component" />
		</router-view>
	</div>
</template>

<script>
import { provide, ref } from "vue"
import { useAuthStore } from "@/stores/auth"

export default {
	name: "Ticketing",
	setup() {
		const authStore = useAuthStore()
		const tickets = ref()
		const ticketTemplates = ref([])
		const ticketController = ref({})

		const impersonateContact = ref()
		provide("impersonateContact", impersonateContact)

		provide("tickets", tickets)
		provide("ticketTemplates", ticketTemplates)
		provide("ticketController", ticketController)

		return {
			authStore,
			tickets,
			ticketTemplates,
			ticketController,
			impersonateContact,
		}
	},
	mounted() {
		if (!this.authStore.isLoggedIn) {
			this.$router.push({
				name: "PortalLogin",
				query: { route: this.$route.path },
			})
		}
		if (this.authStore.isAdmin || this.authStore.isAgent) {
			this.impersonateContact = (contact) => {
				return this.$resources.tickets.fetch({
					impersonate: contact,
				})
			}
		} else {
			this.impersonateContact = () => {
				this.$router.push({ path: "/helpdesk/tickets" })
				this.$resources.tickets.fetch()
			}
		}
		this.ticketController.update = (ticketId) => {
			if (ticketId) {
				this.$resources.ticket.fetch({
					ticket_id: ticketId,
				})
			} else {
				this.$resources.tickets.fetch()
			}
		}
		this.ticketController.newTicket = (values, template, attachments) => {
			this.$resources.createTicket.submit({
				values,
				template,
				attachments,
				via_customer_portal: true,
			})
			return this.$resources.createTicket.loading
		}
		this.ticketController.set = (ticketId, type, ref = null) => {
			switch (type) {
				case "status":
					this.$resources.assignTicketStatus.submit({
						ticket_id: ticketId,
						status: ref,
					})
					break
			}
		}
		this.$socket.on("list_update", (data) => {
			switch (data.doctype) {
				case "Ticket":
					this.ticketController.update()
					break
			}
		})
	},
	resources: {
		tickets() {
			return {
				url: "helpdesk.helpdesk.doctype.hd_ticket.hd_ticket.get_user_tickets",
				auto:
					this.authStore.isLoggedIn && this.$route.name != "Impersonate",
				onSuccess: (data) => {
					this.tickets = {}
					for (var i = 0; i < data.length; i++) {
						this.tickets[data[i].name] = data[i]
					}
				},
			}
		},
		ticket() {
			return {
				url: "helpdesk.api.ticket.get_ticket",
				onSuccess: (ticket) => {
					this.tickets[ticket.name] = ticket
				},
			}
		},
		templates() {
			return {
				url: "helpdesk.api.ticket.get_all_ticket_templates",
				auto: this.authStore.isLoggedIn,
				onSuccess: (data) => {
					this.ticketTemplates = data
				},
			}
		},
		assignTicketStatus() {
			return {
				url: "helpdesk.api.ticket.assign_ticket_status",
				onSuccess: (ticket) => {
					this.ticketController.update(ticket.name)
				},
			}
		},
		createTicket() {
			return {
				url: "helpdesk.api.ticket.create_new",
				onSuccess: (ticket) => {
					this.ticketController.update()
					this.$router.push({
						name: "PortalTicket",
						params: {
							ticketId: ticket.name,
						},
					})
				},
				onError: (error) => {
					this.$toast({
						title: "Error while creating ticket",
						text: error.messages.join(' '),
						icon: "x",
						iconClasses: "text-red-500",
					})
				},
			}
		},
	},
}
</script>
