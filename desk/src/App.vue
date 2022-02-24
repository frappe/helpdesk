<template>
	<div class="w-screen flex">
		<div class="w-15">
			<SideBarMenu />
		</div>
		<div class="flex-col w-full">
			<div class="h-15">
				<NavBar />
			</div>
			<div class="pt-1">
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
import NavBar from "./components/NavBar.vue";
import SideBarMenu from "./components/SideBarMenu.vue";

export default {
	name: "App",
	data() {
		return {
			viewportWidth: 0
		};
	},
	resources: {
		user() {
			return {
				'method': 'helpdesk.api.agent.get_user',
				onSuccess: () => {
					this.$user.set(this.$resources.user.data);
					this.$resources.tickets.fetch()
				},
				onFailure: () => {
					// TODO: use frappe build in login redirect with redirect to helpdesk once logged in
					window.location.replace("/login");
				}
			}
		},
		tickets() {
			return {
				'method': 'helpdesk.api.ticket.get_tickets',
				onSuccess: () => {
					this.$tickets().set({tickets: this.$resources.tickets.data})
				}
			}
		},
		ticket() {
			return {
				method: 'helpdesk.api.ticket.get_ticket',
				onSuccess: () => {
					this.$tickets(this.$resources.ticket.data.name).set(this.$resources.ticket.data)
				}
			}
		},
		createTicket() {
			return {
				method: 'helpdesk.api.ticket.create_new',
				onSuccess: () => {
					// TODO: fix auto refresh list
					this.$tickets().update()
					window.location.reload()
				}
			}
		},
		updateTicketContact() {
			return {
				method: 'helpdesk.api.ticket.update_contact',
				onSuccess: (data) => {
					window.location.reload()
				}
			}
		},
		types() {
			return {
				'method': 'frappe.client.get_list',
				params: {
					doctype: 'Ticket Type',
				},
				auto: true,
				onSuccess: () => {
					this.$tickets().set({types: this.$resources.types.data})
				}
			}
		},
		priorities() {
			return {
				'method': 'frappe.client.get_list',
				params: {
					doctype: 'Ticket Priority',
				},
				auto: true,
				onSuccess: () => {
					this.$tickets().set({priorities: this.$resources.priorities.data})
				}
			}
		},
		contacts() {
			return {
				'method': 'frappe.client.get_list',
				params: {
					doctype: 'Contact',
				},
				auto: true,
				onSuccess: () => {
					this.$tickets().set({contacts: this.$resources.contacts.data})
				}
			}
		},
		statuses() {
			return {
				'method': 'helpdesk.api.ticket.get_all_ticket_statuses',
				auto: true,
				onSuccess: () => {
					this.$tickets().set({statuses: this.$resources.statuses.data})
				}
			}
		},
		agents() {
			return {
				'method': 'frappe.client.get_list',
				params: {
					doctype: 'Agent',
					fields: ['*']
				},
				auto: true,
				onSuccess: () => {
					this.$agents.set(this.$resources.agents.data)
				}
			}
		},
		assignTicketToAgent() {
			return {
				method: 'helpdesk.api.ticket.assign_ticket_to_agent',
				onSuccess: (data) => {
					this.$tickets(data.name).update();
				}
			}
		},
		assignTicketType() {
			return {
				method: 'helpdesk.api.ticket.assign_ticket_type',
				onSuccess: (data) => {
					this.$tickets(data.name).update();
					this.$resources.types.fetch();
				}
			}
		},
		assignTicketStatus() {
			return {
				method: 'helpdesk.api.ticket.assign_ticket_status',
				onSuccess: (data) => {
					this.$tickets(data.name).update();
				}
			}
		},
		assignTicketPriority() {
			return {
				method: 'helpdesk.api.ticket.assign_ticket_priority',
				onSuccess: (data) => {
					this.$tickets(data.name).update()
				}
			}
		},
		createTicketType() {
			return {
				method: 'helpdesk.api.ticket.check_and_create_ticket_type',
				onSuccess: (data) => {
					this.$resources.types.fetch();
				}
			}
		}
	},
	provide: {
		viewportWidth: Math.max(document.documentElement.clientWidth || 0, window.innerWidth || 0)
	},
	components: {
		NavBar,
		SideBarMenu,
	},
	created() {
		const cookie = Object.fromEntries(
			document.cookie
				.split('; ')
				.map(part => part.split('='))
				.map(d => [d[0], decodeURIComponent(d[1])])
		);

		const isLoggedIn = cookie.user_id && cookie.user_id !== 'Guest';

		if (isLoggedIn) {
			this.$resources.user.fetch()
		} else {
			window.location.replace("/login");
		}
	},
	mounted() {
		this.$tickets().setUpdateTickets(() => {
			this.$resources.tickets.fetch()
		})
		this.$tickets().setUpdateTicket((ticketId) => {
			this.$resources.ticket.fetch({
				ticket_id: ticketId,
			})
		})
		this.$tickets().setCreateTicket((values) => {
			this.$resources.createTicket.submit({
				subject: values.subject,
				description: values.description
			})
		})
		this.$tickets().setAssignAgent((ticketId, agentName) => {
			this.$resources.assignTicketToAgent.submit({
				ticket_id: ticketId,
				agent_id: agentName
			})
		})
		this.$tickets().setAssignType((ticketId, type) => {
			this.$resources.assignTicketType.submit({
				ticket_id: ticketId,
				type
			})
		})
		this.$tickets().setAssignStatus((ticketId, status) => {
			this.$resources.assignTicketStatus.submit({
				ticket_id: ticketId,
				status
			})
		})
		this.$tickets().setAssignPriority((ticketId, priority) => {
			this.$resources.assignTicketPriority.submit({
				ticket_id: ticketId,
				priority
			})
		})
		this.$tickets().setCreateType((type) => {
			this.$resources.createTicketType.submit({
				type
			})
		})
		this.$tickets().setUpdateContact((ticketId, contact) => {
			this.$resources.updateTicketContact.submit({
				ticket_id: ticketId,
				contact
			})
		})
		this.$socket.on("list_update", (data) => {
			if (data.doctype == "Ticket") {
				this.$tickets(data.name).update();
			}
			// TODO: handle other doctype events too
		})
	}
}
</script>