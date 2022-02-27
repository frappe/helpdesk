<template>
	<div v-if="user.isLoggedIn()" class="w-screen flex">
		<div class="w-15">
			<SideBarMenu />
		</div>
		<div class="flex-col w-full">
			<div class="h-15">
				<NavBar />
			</div>
			<div>
				<router-view v-slot="{ Component }">
					<keep-alive>
						<component :is="Component" />
					</keep-alive>
				</router-view>
			</div>
		</div>
	</div>
</template>
<script>
import NavBar from "@/components/desk/NavBar.vue"
import SideBarMenu from "@/components/desk/SideBarMenu.vue"
import { inject, provide, ref } from 'vue'

export default {
	name: "Desk",
	components: {
		NavBar,
		SideBarMenu,
	},
	setup() {
		const user = inject('user')

		const tickets = ref({})
		const ticketTypes = ref([])
		const ticketPriorities = ref([])
		const ticketStatuses = ref([])

		const ticketController = ref({})

		const contacts = ref([])
		const contactController = ref({})
		
		const agents = ref([])
		const agentController = ref({})
		
		provide('tickets', tickets)
		provide('ticketTypes', ticketTypes)
		provide('ticketPriorities', ticketPriorities)
		provide('ticketStatuses', ticketStatuses)

		provide('ticketController', ticketController)

		provide('contacts', contacts)
		provide('contactController', contactController)

		provide('agents', agents)
		provide('agentController', agentController)

		return {
			user,

			tickets,
			ticketTypes,
			ticketPriorities,
			ticketStatuses,

			ticketController,

			contacts,
			contactController,

			agents,
			agentController
		}
	},
	mounted() {
		this.ticketController.update = (ticketId) => {
			if (ticketId) {
				this.$resources.ticket.fetch({
					ticket_id: ticketId
				})
			} else {
				this.$resources.tickets.fetch()
			}
		},
		this.ticketController.set = (ticketId, type, ref=null) => {
			switch (type) {
				case 'type':
					this.$resources.assignTicketType.submit({
						ticket_id: ticketId,
						type: ref
					})
					break
				case 'status':
					this.$resources.assignTicketStatus.submit({
						ticket_id: ticketId,
						status: ref
					})
					break
				case 'priority':
					this.$resources.assignTicketPriority.submit({
						ticket_id: ticketId,
						priority: ref
					})
					break
				case 'agent':
					this.$resources.assignTicketToAgent.submit({
						ticket_id: ticketId,
						agent_id: ref
					})
					break
			}
		},
		this.ticketController.new = (type, value) => {
			switch (type) {
				case 'ticket':
					this.$resources.createTicket.submit({
						subject: value.subject,
						description: value.description
					})
					break
				case 'type':
					this.$resources.createTicketType.subject({
						type: value
					})
					break
			}
		}
		this.$socket.on("list_update", (data) => {
			switch (data.doctype) {
				case 'Ticket':
					this.ticketController.update()
					break
				case 'Ticket Type':
					this.$resources.type.fetch()
					break
				case 'Contact':
					this.$resources.contacts.fetch()
				case 'Agent':
					this.$resources.agents.fetch()
			}
		})
	},
	unmounted() {
		this.$socket.off('list_update')
	},
	resources: {
		tickets() {
			return {
				method: 'helpdesk.api.ticket.get_tickets',
				auto: true,
				onSuccess: (data) => {
					// TODO: do this using an inline method
					this.tickets = {}
					for (var i = 0; i < data.length; i++) {
						this.tickets[data[i].name] = data[i]
					}
				},
				onFailure: () => {
					// TODO:
				}
			}
		},
		ticket() {
			return {
				method: 'helpdesk.api.ticket.get_ticket',
				onSuccess: (ticket) => {
					this.tickets[ticket.name] = ticket
				},
				onFailure: () => {
					// TODO:
				}
			}
		},
		createTicket() {
			return {
				method: 'helpdesk.api.ticket.create_new',
				onSuccess: () => {
					this.ticketController.update()
				},
				onFailure: () => {
					// TODO:
				}
			}
		},
		updateTicketContact() {
			return {
				method: 'helpdesk.api.ticket.update_contact',
				onSuccess: (ticket) => {
					this.ticketController.update(ticket.name)
				},
				onFailure: () => {
					// TODO:
				}
			}
		},
		types() {
			return {
				method: 'frappe.client.get_list',
				params: {
					doctype: 'Ticket Type',
					pluck: 'name'
				},
				auto: true,
				onSuccess: (data) => {
					this.ticketTypes = data
				},
				onFailure: () => {
					// TODO:
				}
			}
		},
		priorities() {
			return {
				method: 'frappe.client.get_list',
				params: {
					doctype: 'Ticket Priority',
				},
				auto: true,
				onSuccess: (data) => {
					this.ticketPriorities = data
				},
				onFailure: () => {
					// TODO:
				}
			}
		},
		statuses() {
			return {
				method: 'helpdesk.api.ticket.get_all_ticket_statuses',
				auto: true,
				onSuccess: (data) => {
					this.ticketStatuses = data
				},
				onFailure: () => {
					// TODO:
				}
			}
		},
		contacts() {
			return {
				method: 'frappe.client.get_list',
				params: {
					doctype: 'Contact',
				},
				auto: true,
				onSuccess: (data) => {
					this.contacts = data
				},
				onFailure: () => {
					// TODO:
				}
			}
		},
		agents() {
			return {
				method: 'frappe.client.get_list',
				params: {
					doctype: 'Agent',
					fields: ['*']
				},
				auto: true,
				onSuccess: (data) => {
					this.agents = data
				},
				onFailure: () => {
					// TODO:
				}
			}
		},
		assignTicketToAgent() {
			return {
				method: 'helpdesk.api.ticket.assign_ticket_to_agent',
				onSuccess: (ticket) => {
					this.ticketController.update(ticket.name)
				},
				onFailure: () => {
					// TODO:
				}
			}
		},
		assignTicketType() {
			return {
				method: 'helpdesk.api.ticket.assign_ticket_type',
				onSuccess: (ticket) => {
					this.ticketController.update(ticket.name)
				},
				onFailure: () => {
					// TODO:
				}
			}
		},
		assignTicketStatus() {
			return {
				method: 'helpdesk.api.ticket.assign_ticket_status',
				onSuccess: (ticket) => {
					this.ticketController.update(ticket.name)
				},
				onFailure: () => {
					// TODO:
				}
			}
		},
		assignTicketPriority() {
			return {
				method: 'helpdesk.api.ticket.assign_ticket_priority',
				onSuccess: (ticket) => {
					this.ticketController.update(ticket.name)
				},
				onFailure: () => {
					// TODO:
				}
			}
		},
		createTicketType() {
			return {
				method: 'helpdesk.api.ticket.check_and_create_ticket_type',
				onSuccess: () => {
					this.$resources.types.fetch();
				},
				onFailure: () => {
					// TODO:
				}
			}
		}
	}
}
</script>