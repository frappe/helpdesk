<template>
	<div
		v-if="authStore.isLoggedIn && authStore.hasDeskAccess"
		class="h-screen w-screen"
	>
		<div v-if="initialized">
			<div class="flex h-screen w-screen flex-row">
				<SideBar />
				<router-view :key="$route.fullPath" class="z-0 grow" />
			</div>
		</div>
		<div v-else class="flex h-full w-full max-w-full grow-0">
			<div class="m-auto text-base font-normal">
				<CustomIcons name="frappedesk" class="w-[200px]" />
			</div>
		</div>
	</div>
</template>

<script>
import { provide, ref } from "vue";
import SideBar from "@/components/desk/sidebar/SideBar.vue";
import CustomIcons from "@/components/desk/global/CustomIcons.vue";
import { useAuthStore } from "@/stores/auth";

export default {
	name: "Desk",
	components: {
		SideBar,
		CustomIcons,
	},
	setup() {
		const mounted = ref(false);
		const authStore = useAuthStore();

		const ticketTypes = ref([]);
		const ticketPriorities = ref([]);
		const ticketStatuses = ref([]);

		const ticketController = ref({});

		const contacts = ref([]);
		const contactController = ref({});

		const agents = ref([]);
		const agentGroups = ref([]);
		const agentController = ref({});

		provide("ticketTypes", ticketTypes);
		provide("ticketPriorities", ticketPriorities);
		provide("ticketStatuses", ticketStatuses);

		provide("ticketController", ticketController);

		provide("contacts", contacts);
		provide("contactController", contactController);

		provide("agents", agents);
		provide("agentGroups", agentGroups);
		provide("agentController", agentController);

		return {
			mounted,
			authStore,

			ticketTypes,
			ticketPriorities,
			ticketStatuses,

			ticketController,

			contacts,
			contactController,

			agents,
			agentGroups,
			agentController,
		};
	},
	computed: {
		initialized() {
			if (!this.mounted) return false;
			if (!this.authStore.isLoggedIn) return false;
			if (!this.authStore.hasDeskAccess) return false;
			if (this.$resources.helpdeskSettings.loading) return false;
			if (!this.$resources.helpdeskSettings.data.initial_agent_set) {
				this.$resources.setupInitialAgent.submit();
				return false;
			}
			if (
				!this.$resources.helpdeskSettings.data.initial_demo_ticket_created
			) {
				this.$resources.createInitialDemoTicket.submit();
				return false;
			}

			return true;
		},
		defaultOutgoingEmailAccountSetup() {
			if (this.$resources.defaultOutgoingEmailAccount.loading) {
				return "NOT SET";
			}
			return this.$resources.defaultOutgoingEmailAccount.data > 0;
		},
	},
	watch: {
		initialized(val) {
			if (val) {
				this.handlePostOnboardSetupReqs();
			}
		},
	},
	mounted() {
		if (!this.authStore.isLoggedIn) {
			this.$router.push({
				name: "DeskLogin",
				query: { route: this.$route.path },
			});
			return;
		}
		if (!this.authStore.hasDeskAccess) {
			this.$router.push({ path: "/my-tickets" });
			return;
		}
		this.$resources.helpdeskSettings.fetch();
		this.ticketController.set = (ticketId, type, ref = null) => {
			switch (type) {
				case "type":
					return this.$resources.assignTicketType.submit({
						ticket_id: ticketId,
						type: ref,
					});
				case "status":
					return this.$resources.assignTicketStatus.submit({
						ticket_id: ticketId,
						status: ref,
					});
				case "priority":
					return this.$resources.assignTicketPriority.submit({
						ticket_id: ticketId,
						priority: ref,
					});
				case "contact":
					return this.$resources.updateTicketContact.submit({
						ticket_id: ticketId,
						contact: ref,
					});
				case "agent":
					return this.$resources.assignTicketToAgent.submit({
						ticket_id: ticketId,
						agent_id: ref,
					});
			}
		};
		this.ticketController.new = (type, values) => {
			switch (type) {
				case "ticket":
					return this.$resources.createTicket.submit({
						values,
					});
				case "type":
					this.$resources.createTicketType.submit({
						type: values,
					});
					break;
			}
		};
		this.$socket.on("list_update", (data) => {
			switch (data.doctype) {
				case "HD Ticket Type":
					this.$resources.types.reload();
					break;
				case "HD Agent":
					this.$resources.agents.reload();
					break;
			}
		});

		this.mounted = true;
	},
	unmounted() {
		this.$socket.off("list_update");
	},
	methods: {
		handlePostOnboardSetupReqs() {
			// helpdesk name
			if (
				!this.$resources.helpdeskSettings.data.helpdesk_name &&
				!this.$resources.helpdeskSettings.data
					.initial_helpdesk_name_setup_skipped
			) {
				this.showHelpdeskNameSetupToast();
				return;
			}
			// default email account
			if (
				!this.$resources.helpdeskSettings.data.suppress_default_email_toast &&
				this.defaultOutgoingEmailAccountSetup != "NOT SET" &&
				!this.defaultOutgoingEmailAccountSetup
			) {
				this.showDefaultEmailAccountSetupToast();
				return;
			}
			// add agents
			if (
				!this.$resources.agentCount.loading &&
				this.$resources.agentCount.data == 0
			) {
				// this block should theoretically never fire, since the initial agent is created during the setup process
				this.showAddAgentsToast();
			}
		},
		showHelpdeskNameSetupToast() {
			this.$toast({
				title: "Set a name",
				text: "What would you like to name your helpdesk?",
				timeout: 0,
				icon: "edit",
				iconClasses: "text-blue-500",
				form: {
					classes: "flex gap-1",
					inputs: [
						{
							type: "text",
							fieldname: "helpdeskName",
							placeholder: "Frappe Helpdesk",
						},
					],
					onSubmit: (values) => {
						const inputs = values.target?.elements;
						const name = inputs?.helpdeskName?.value;

						if (!name) return;

						this.$resources.setHelpdeskName.submit({
							name,
						});
					},
				},
				actionOnClose: () => {
					this.$resources.skipHelpdeskNameSetup.submit();
				},
			});
		},
		showDefaultEmailAccountSetupToast() {
			this.$toast({
				title: "Default outgoing email account not added",
				text: "Please add a default outgoing email account in settings.",
				timeout: 0,
				icon: "mail",
				iconClasses: "text-red-500",
				buttons: [
					{
						title: "Setup now",
						appearance: "primary",
						iconRight: "arrow-right",
						onClick: () => {
							this.$router.push({ name: "Emails" });
						},
					},
				],
			});
		},
		showAddAgentsToast() {
			this.$toast({
				title: "Add agent",
				text: "Please add an agent from settings",
				timeout: 0,
				appearance: "info",
				icon: "users",
				iconClasses: "text-red-500",
				buttons: [
					{
						title: "Add now",
						appearance: "danger",
						iconRight: "arrow-right",
						onClick: () => {
							this.$router.push({ name: "Agents" });
						},
					},
				],
			});
		},
	},
	resources: {
		// onboarding related resources
		// setters
		setupInitialAgent() {
			// sets up an initial agent
			return {
				url: "helpdesk.api.setup.initial_agent_setup",
				onSuccess: (res) => {
					this.$resources.helpdeskSettings.fetch();
				},
				onError: (err) => {
					this.$toast({
						title: "Something went wrong, while adding initial agent",
						text: "Please try again later.",
						icon: "x",
						iconClasses: "text-red-500",
					});
				},
			};
		},
		createInitialDemoTicket() {
			// creates a demo ticket
			return {
				url: "helpdesk.api.setup.create_initial_demo_ticket",
				onSuccess: (res) => {
					this.$resources.helpdeskSettings.fetch();
				},
				onError: (err) => {
					this.$toast({
						title: "Something went wrong, while creating a demo ticket",
						text: "Please try again later.",
						icon: "x",
						iconClasses: "text-red-500",
					});
				},
			};
		},
		setHelpdeskName() {
			// set helpdesk name in Helpdesk Settings
			return {
				url: "helpdesk.api.settings.update_helpdesk_name",
				onSuccess: (res) => {
					document.title = `Helpdesk ${res ? ` | ${res}` : ""}`;
					this.$toast({
						title: "Helpdesk name updated!!",
						icon: "check",
						iconClasses: "text-green-500",
					});
				},
				onError: (err) => {
					this.$toast({
						title: "Something went wrong, updating helpdesk name",
						text: "Please try again later.",
						icon: "x",
						iconClasses: "text-red-500",
					});
				},
			};
		},
		skipHelpdeskNameSetup() {
			// sets the values of skip_helpdesk_name_setup to true inside Helpdesk Settings
			return {
				url: "helpdesk.api.settings.skip_helpdesk_name_setup",
			};
		},
		// getters
		helpdeskSettings() {
			return {
				url: "frappe.client.get",
				params: {
					doctype: "HD Settings",
					name: "HD Settings",
				},
				onError: (error) => {
					this.$toast({
						title: "Something went wrong.",
						text: "Please try again later.",
						icon: "x",
						iconClasses: "text-red-500",
					});
				},
			};
		},
		defaultOutgoingEmailAccount() {
			return {
				url: "frappe.client.get_count",
				params: {
					doctype: "Email Account",
					filters: [
						["use_imap", "=", 1],
						["IMAP Folder", "append_to", "=", "HD Ticket"],
						["default_outgoing", "=", 1],
					],
				},
				auto: true,
			};
		},
		agentCount() {
			return {
				url: "frappe.client.get_count",
				params: {
					doctype: "HD Agent",
				},
				auto: true,
			};
		},

		// ticket related resources
		createTicket() {
			return {
				url: "helpdesk.api.ticket.create_new",
				onSuccess: () => {
					// TODO:
				},
				onError: (error) => {
					this.$toast({
						title: "Error while creating ticket",
						text: error.messages.join(", "),
						icon: "x",
						iconClasses: "text-red-500",
					});

					throw error;
				},
			};
		},
		updateTicketContact() {
			return {
				url: "helpdesk.api.ticket.update_contact",
				onSuccess: async (ticket) => {
					// TODO:
				},
				onError: () => {
					// TODO:
				},
			};
		},
		types() {
			return {
				url: "helpdesk.extends.client.get_list",
				params: {
					doctype: "HD Ticket Type",
					pluck: "name",
				},
				auto: this.authStore.hasDeskAccess,
				onSuccess: (data) => {
					this.ticketTypes = data;
				},
				onError: () => {
					// TODO:
				},
			};
		},
		priorities() {
			return {
				url: "helpdesk.extends.client.get_list",
				params: {
					doctype: "HD Ticket Priority",
				},
				auto: this.authStore.hasDeskAccess,
				onSuccess: (data) => {
					this.ticketPriorities = data;
				},
				onError: () => {
					// TODO:
				},
			};
		},
		statuses() {
			return {
				url: "helpdesk.api.ticket.get_all_ticket_statuses",
				auto: this.authStore.hasDeskAccess,
				onSuccess: (data) => {
					this.ticketStatuses = data;
				},
				onError: () => {
					// TODO:
				},
			};
		},
		contacts() {
			return {
				url: "helpdesk.extends.client.get_list",
				params: {
					doctype: "Contact",
					fields: ["*"],
					limit_page_length: 0,
				},
				auto: this.authStore.hasDeskAccess,
				onSuccess: (data) => {
					this.contacts = data;
				},
				onError: () => {
					// TODO:
				},
			};
		},
		agents() {
			return {
				url: "helpdesk.extends.client.get_list",
				params: {
					doctype: "HD Agent",
					fields: ["name", "agent_name", "user_image"],
				},
				auto: this.authStore.hasDeskAccess,
				onSuccess: (data) => {
					this.agents = data;
				},
				onError: () => {
					// TODO:
				},
			};
		},
		agentGroups() {
			return {
				url: "helpdesk.extends.client.get_list",
				params: {
					doctype: "HD Team",
				},
				auto: this.authStore.hasDeskAccess,
				onSuccess: (data) => {
					this.agentGroups = data;
				},
				onError: () => {
					// TODO:
				},
			};
		},
		assignTicketToAgent() {
			return {
				url: "helpdesk.api.ticket.assign_ticket_to_agent",
				onSuccess: async () => {
					this.$event.emit("update_ticket_list");
				},
				onError: () => {
					// TODO:
				},
			};
		},
		assignTicketType() {
			return {
				url: "helpdesk.api.ticket.assign_ticket_type",
				onSuccess: async (ticket) => {},
				onError: () => {
					// TODO:
				},
			};
		},
		assignTicketStatus() {
			return {
				url: "helpdesk.api.ticket.assign_ticket_status",
				onSuccess: async () => {
					this.$event.emit("update_ticket_list");
				},
				onError: () => {
					// TODO:
				},
			};
		},
		assignTicketPriority() {
			return {
				url: "helpdesk.api.ticket.assign_ticket_priority",
				onSuccess: async (ticket) => {},
				onError: () => {
					// TODO:
				},
			};
		},
		createTicketType() {
			return {
				url: "helpdesk.api.ticket.check_and_create_ticket_type",
				onSuccess: () => {
					this.$resources.types.fetch();
				},
				onError: () => {
					// TODO:
				},
			};
		},
	},
	directivs: {},
};
</script>
