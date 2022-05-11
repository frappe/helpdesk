<template>
	<div v-if="user.isLoggedIn() && user.has_desk_access" class="w-screen">
		<div class="flex w-screen">
			<div class="bg-gray-50 w-[182px] shrink-0">
				<SideBarMenu />
			</div>
			<div class="grow">
				<router-view v-slot="{ Component }">
					<component :is="Component" />
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

		const tickets = ref('')
		const ticketTypes = ref([])
		const ticketPriorities = ref([])
		const ticketStatuses = ref([])

		const ticketController = ref({})

		const contacts = ref([])
		const contactController = ref({})
		
		const agents = ref([])
		const agentGroups = ref([])
		const agentController = ref({})

		const updateSidebarFilter = ref(() => {})

		
		provide('tickets', tickets)
		provide('ticketTypes', ticketTypes)
		provide('ticketPriorities', ticketPriorities)
		provide('ticketStatuses', ticketStatuses)

		provide('ticketController', ticketController)

		provide('contacts', contacts)
		provide('contactController', contactController)

		provide('agents', agents)
		provide('agentGroups', agentGroups)
		provide('agentController', agentController)

		provide('updateSidebarFilter', updateSidebarFilter)

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
			agentGroups,
			agentController
		}
	},
	mounted() {
		if (!this.user.isLoggedIn()) {
			this.$router.push({name: "DeskLogin"})
			return
		}
		if (!this.user.has_desk_access) {
			this.$router.push({path: "/support/tickets"})
			return
		}

		this.ticketController.update = (ticketId) => {
			if (ticketId) {
				return this.$resources.ticket.fetch({
					ticket_id: ticketId
				})
			} else {
				return this.$resources.tickets.fetch()
			}
		},
		this.ticketController.markAsSeen = (ticketId) => {
			this.$resources.markTicketAsSeen.submit({
				ticket_id: ticketId
			})
		}
		this.ticketController.set = (ticketId, type, ref=null) => {
			switch (type) {
				case 'type':
					return this.$resources.assignTicketType.submit({
						ticket_id: ticketId,
						type: ref
					})
				case 'status':
					return this.$resources.assignTicketStatus.submit({
						ticket_id: ticketId,
						status: ref
					})
				case 'priority':
					return this.$resources.assignTicketPriority.submit({
						ticket_id: ticketId,
						priority: ref
					})
				case 'contact':
					return this.$resources.updateTicketContact.submit({
						ticket_id: ticketId,
						contact: ref
					})
				case 'agent':
					return this.$resources.assignTicketToAgent.submit({
						ticket_id: ticketId,
						agent_id: ref
					})
				case 'group':
					return this.$resources.assignTicketGroup.submit({
						ticket_id: ticketId,
						agent_group: ref
					})
				case 'notes':
					return this.$resources.setTicketNotes.submit({
						ticket_id: ticketId,
						notes: ref
					})
			}
		},
		this.ticketController.bulkSet = (ticketIds, type, ref=null) => {
			switch (type) {
				case 'status':
					return this.$resources.bulkAssignTicketStatus.submit({
						ticket_ids: ticketIds,
						status: ref
					})
				case 'agent':
					return this.$resources.bulkAssignTicketToAgent.submit({
						ticket_ids: ticketIds,
						agent_id: ref
					})
			}
		},
		this.ticketController.new = (type, values) => {
			switch (type) {
				case 'ticket':
					return this.$resources.createTicket.submit({
						values
					})
				case 'type':
					this.$resources.createTicketType.submit({
						type: values
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
					this.$resources.types.fetch()
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
				method: 'frappedesk.api.ticket.get_tickets',
				auto: this.user.has_desk_access,
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
				method: 'frappedesk.api.ticket.get_ticket',
				onSuccess: (ticket) => {
					this.tickets[ticket.name] = ticket
				},
				onFailure: () => {
					// TODO:
				}
			}
		},
		markTicketAsSeen() {
			return {
				method: 'frappedesk.api.ticket.mark_ticket_as_seen',
				onSuccess: () => {
					this.ticketController.update()
				},
				onFailure: () => {

				}
			}
		},
		createTicket() {
			return {
				method: 'frappedesk.api.ticket.create_new',
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
				method: 'frappedesk.api.ticket.update_contact',
				onSuccess: async (ticket) => {
					await this.ticketController.markAsSeen(ticket.name)
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
				auto: this.user.has_desk_access,
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
				auto: this.user.has_desk_access,
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
				method: 'frappedesk.api.ticket.get_all_ticket_statuses',
				auto: this.user.has_desk_access,
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
					fields: ['*'],
					limit_page_length: 0
				},
				auto: this.user.has_desk_access,
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
				auto: this.user.has_desk_access,
				onSuccess: (data) => {
					this.agents = data
				},
				onFailure: () => {
					// TODO:
				}
			}
		},
		agentGroups() {
			return {
				method: 'frappe.client.get_list',
				params: {
					doctype: 'Agent Group'
				},
				auto: this.user.has_desk_access,
				onSuccess: (data) => {
					this.agentGroups = data
				},
				onFailure: () => {
					// TODO:
				}
			}
		},
		assignTicketToAgent() {
			return {
				method: 'frappedesk.api.ticket.assign_ticket_to_agent',
				onSuccess: async (ticket) => {
					await this.ticketController.markAsSeen(ticket.name)
					this.ticketController.update(ticket.name)
				},
				onFailure: () => {
					// TODO:
				}
			}
		},
		bulkAssignTicketToAgent() {
			return {
				method: 'frappedesk.api.ticket.bulk_assign_ticket_to_agent',
				onSuccess: (ticket) => {
					// TODO: do bulk update
					this.ticketController.update()
				},
				onFailure: () => {
					// TODO:
				}
			}
		},
		assignTicketType() {
			return {
				method: 'frappedesk.api.ticket.assign_ticket_type',
				onSuccess: async (ticket) => {
					await this.ticketController.markAsSeen(ticket.name)
					this.ticketController.update(ticket.name)
				},
				onFailure: () => {
					// TODO:
				}
			}
		},
		assignTicketStatus() {
			return {
				method: 'frappedesk.api.ticket.assign_ticket_status',
				onSuccess: async (ticket) => {
					await this.ticketController.markAsSeen(ticket.name)
					this.ticketController.update(ticket.name)
				},
				onFailure: () => {
					// TODO:
				}
			}
		},
		bulkAssignTicketStatus() {
			return {
				method: 'frappedesk.api.ticket.bulk_assign_ticket_status',
				onSuccess: (tickets) => {
					// TODO: do bulk update for tickets
					this.ticketController.update()
				},
				onFailure: () => {
					// TODO:
				}
			}
		},
		assignTicketPriority() {
			return {
				method: 'frappedesk.api.ticket.assign_ticket_priority',
				onSuccess: async (ticket) => {
					await this.ticketController.markAsSeen(ticket.name)
					this.ticketController.update(ticket.name)
				},
				onFailure: () => {
					// TODO:
				}
			}
		},
		assignTicketGroup() {
			return {
				method: 'frappedesk.api.ticket.assign_ticket_group',
				onSuccess: async (ticket) => {
					await this.ticketController.markAsSeen(ticket.name)
					this.ticketController.update(ticket.name)
				},
				onFailure: () => {
					// TODO:
				}
			}
		},
		createTicketType() {
			return {
				method: 'frappedesk.api.ticket.check_and_create_ticket_type',
				onSuccess: () => {
					this.$resources.types.fetch();
				},
				onFailure: () => {
					// TODO:
				}
			}
		},
		setTicketNotes() {
			return {
				method: 'frappedesk.api.ticket.set_ticket_notes',
				onSuccess: async (ticket) => {
					await this.ticketController.markAsSeen(ticket.name)
					this.ticketController.update(ticket.name)
				},
				onFailure: () => {

				}
			}
		}
	},
	directivs: {
		
	}
}
</script>