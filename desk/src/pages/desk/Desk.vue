<template>
	<div v-if="user.isLoggedIn() && user.has_desk_access" class="w-screen">
		<div class="flex flex-row w-screen">
			<SideBarMenu class="bg-gray-50 shrink-0 w-[241px]" />
			<router-view class="grow" />
		</div>
	</div>
</template>
<script>
import SideBarMenu from "@/components/desk/SideBarMenu.vue"
import { inject, provide, ref } from 'vue'

export default {
	name: "Desk",
	components: {
		SideBarMenu,
	},
	setup() {
		const user = inject('user')

		const ticketTypes = ref([])
		const ticketPriorities = ref([])
		const ticketStatuses = ref([])

		const ticketController = ref({})

		const contacts = ref([])
		const contactController = ref({})
		
		const agents = ref([])
		const agentGroups = ref([])
		const agentController = ref({})

		const sideBarFilterMap = ref({
			'all': 'All Tickets',
			'my-open-tickets': 'My Open Tickets',
			'my-replied-tickets': 'My Replied Tickets',
			'my-resolved-tickets': 'My Resolved Tickets',
			'my-closed-tickets': 'My Closed Tickets',
		})
		provide('sideBarFilterMap', sideBarFilterMap)
		
		const ticketSideBarFilter = ref('all')
		provide('ticketSideBarFilter', ticketSideBarFilter)
		
		
		provide('ticketTypes', ticketTypes)
		provide('ticketPriorities', ticketPriorities)
		provide('ticketStatuses', ticketStatuses)

		provide('ticketController', ticketController)

		provide('contacts', contacts)
		provide('contactController', contactController)

		provide('agents', agents)
		provide('agentGroups', agentGroups)
		provide('agentController', agentController)

		return {
			user,

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
			this.$router.push({name: "DeskLogin", query:{route: this.$route.path}})
			return
		}
		if (!this.user.has_desk_access) {
			this.$router.push({path: "/support/tickets"})
			return
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
				case 'Ticket Type':
					this.$resources.types.reload()
					break
				case 'Contact':
					this.$resources.contacts.reload()
					break
				case 'Agent':
					this.$resources.agents.reload()
					break
			}
		})
	},
	unmounted() {
		this.$socket.off('list_update')
	},
	resources: {
		createTicket() {
			return {
				method: 'frappedesk.api.ticket.create_new',
				onSuccess: () => {
					// TODO:
				},
				onError: () => {
					// TODO:
				}
			}
		},
		updateTicketContact() {
			return {
				method: 'frappedesk.api.ticket.update_contact',
				onSuccess: async (ticket) => {
					// TODO: 
				},
				onError: () => {
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
				onError: () => {
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
				onError: () => {
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
				onError: () => {
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
				onError: () => {
					// TODO:
				}
			}
		},
		agents() {
			return {
				type: 'list',
				doctype: 'Agent',
				cache: ['Desk', 'Agents'],
				fields: [
					'name',
					'agent_name',
					// TODO: 'user.user_image'
				],
				onSuccess: (data) => {
					this.agents = data
				},
				onError: () => {
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
				onError: () => {
					// TODO:
				}
			}
		},
		assignTicketToAgent() {
			return {
				method: 'frappedesk.api.ticket.assign_ticket_to_agent',
				onSuccess: async () => {
					this.$event.emit('update_ticket_list')
				},
				onError: () => {
					// TODO:
				}
			}
		},
		assignTicketType() {
			return {
				method: 'frappedesk.api.ticket.assign_ticket_type',
				onSuccess: async (ticket) => {

				},
				onError: () => {
					// TODO:
				}
			}
		},
		assignTicketStatus() {
			return {
				method: 'frappedesk.api.ticket.assign_ticket_status',
				onSuccess: async () => {
					this.$event.emit('update_ticket_list')
				},
				onError: () => {
					// TODO:
				}
			}
		},
		assignTicketPriority() {
			return {
				method: 'frappedesk.api.ticket.assign_ticket_priority',
				onSuccess: async (ticket) => {

				},
				onError: () => {
					// TODO:
				}
			}
		},
		assignTicketGroup() {
			return {
				method: 'frappedesk.api.ticket.assign_ticket_group',
				onSuccess: async (ticket) => {

				},
				onError: () => {
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
				onError: () => {
					// TODO:
				}
			}
		},
		setTicketNotes() {
			return {
				method: 'frappedesk.api.ticket.set_ticket_notes',
				onSuccess: async (ticket) => {
					
				},
				onError: () => {

				}
			}
		}
	},
	directivs: {
		
	}
}
</script>