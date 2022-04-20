<template>
	<div>
		<div class="h-15 mb-5">
			<NavBar />
		</div>
		<div class="mb-10">
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
						<Button appearance="primary" @click="this.$router.push({name: 'PortalLogin'})">Login to continue</Button>
					</div>
				</div>
			</div>
		</div>
	</div>
</template>

<script>
import { inject, provide, ref } from 'vue'
import NavBar from '@/components/portal/NavBar.vue'
import Footer from '@/components/portal/Footer.vue';

export default {
	name: "App",
	setup() {
		const user = inject("user");
		const tickets = ref();
		const ticketStatuses = ref([]);
		const ticketTemplates = ref([]);
		const ticketController = ref({});
		provide("tickets", tickets);
		provide("ticketStatuses", ticketStatuses);
		provide("ticketTemplates", ticketTemplates);
		provide("ticketController", ticketController);
		return { user, tickets, ticketStatuses, ticketTemplates, ticketController };
	},
	mounted() {
		this.ticketController.createTicket = ((template = "Default") => {
			console.log("create ticket");
		});
		this.ticketController.update = (ticketId) => {
			if (ticketId) {
				this.$resources.ticket.fetch({
					ticket_id: ticketId
				});
			}
			else {
				this.$resources.tickets.fetch();
			}
		};
		this.ticketController.newTicket = (values, template) => {
			this.$resources.createTicket.submit({ values, template });
			return this.$resources.createTicket.loading;
		};
		this.ticketController.set = (ticketId, type, ref = null) => {
			switch (type) {
				case "status":
					this.$resources.assignTicketStatus.submit({
						ticket_id: ticketId,
						status: ref
					});
					break;
			}
		};
		this.$socket.on("list_update", (data) => {
			switch (data.doctype) {
				case "Ticket":
					this.ticketController.update();
					break;
			}
		});
	},
	resources: {
		tickets() {
			return {
				method: "frappedesk.frappedesk.doctype.ticket.ticket.get_user_tickets",
				auto: true,
				onSuccess: (data) => {
					this.tickets = {};
					for (var i = 0; i < data.length; i++) {
						this.tickets[data[i].name] = data[i];
					}
				},
				onFailure: (error) => {
					console.log(`tickets error : ${error}`);
				}
			};
		},
		ticket() {
			return {
				method: "frappedesk.api.ticket.get_ticket",
				onSuccess: (ticket) => {
					this.tickets[ticket.name] = ticket;
				},
				onFailure: (error) => {
					console.log(`ticket error : ${error}`);
				}
			};
		},
		statuses() {
			return {
				method: "frappedesk.api.ticket.get_all_ticket_statuses",
				auto: true,
				onSuccess: (data) => {
					this.ticketStatuses = data;
				},
                onFailure: (error) => {
                    console.log(`statuses error : ${error}`);
                }
			};
		},
		templates() {
			return {
				method: "frappedesk.api.ticket.get_all_ticket_templates",
				auto: true,
				onSuccess: (data) => {
					this.ticketTemplates = data;
				},
                onFailure: (error) => {
                    console.log(`template error : ${error}`);
                }
			};
		},
		assignTicketStatus() {
			return {
				method: "frappedesk.api.ticket.assign_ticket_status",
				onSuccess: (ticket) => {
					this.ticketController.update(ticket.name);
				},
                onFailure: (error) => {
                    console.log(`assign status error : ${error}`);
                }
			};
		},
		createTicket() {
			return {
				method: "frappedesk.api.ticket.create_new",
				onSuccess: (ticket) => {
					this.ticketController.update();
					this.$router.push({
						name: "PortalTicket",
						params: {
							ticketId: ticket.name
						}
					});
				},
                onFailure: (error) => {
                    console.log(`create ticket error : ${error}`);
                }
			};
		},
	},
	components: { NavBar, Footer }
}
</script>