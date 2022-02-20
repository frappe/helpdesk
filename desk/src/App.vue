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
				auto: true,
				onSuccess: () => {
					this.$user.set(this.$resources.user.data);
				}
			}
		},
		tickets() {
			return {
				'method': 'helpdesk.api.ticket.get_tickets',
				auto: true,
				onSuccess: () => {
					this.$tickets().set({tickets: this.$resources.tickets.data})
				}
			}
		},
		ticket() {
			return {
				method: 'helpdesk.api.ticket.get_ticket',
				onSuccess: () => {
					console.log("fetched ticket!!")
					this.$tickets(this.$resources.ticket.data.name).set(this.$resources.ticket.data)
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
		}
	},
	provide: {
		viewportWidth: Math.max(document.documentElement.clientWidth || 0, window.innerWidth || 0)
	},
	components: {
		NavBar,
		SideBarMenu,
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
		this.$socket.on("list_update", (data) => {
			if (data.doctype == "Ticket") {
				this.$tickets(data.name).update();
			}
			// TODO: handle other doctype events too
		})
	}
}
</script>