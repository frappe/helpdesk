<template>
	<div
		v-if="user.isLoggedIn() && user.has_desk_access"
		class="w-screen h-screen"
	>
		<div v-if="initialized">
			<div class="flex flex-row w-screen">
				<SideBarMenu class="bg-gray-50 shrink-0 w-[200px]" />
				<router-view class="grow" :key="$route.fullPath" />
			</div>
		</div>
		<div v-else class="h-full w-full flex max-w-full grow-0">
			<div class="mx-auto my-auto text-base font-normal">
				<CustomIcons name="helpdesk" class="w-[200px]" />
			</div>
		</div>
	</div>
</template>
<script>
import SideBarMenu from "@/components/desk/SideBarMenu.vue"
import { inject, provide, ref } from "vue"
import CustomIcons from "@/components/desk/global/CustomIcons.vue"

export default {
	name: "Desk",
	components: {
		SideBarMenu,
		CustomIcons,
	},
	setup() {
		const mounted = ref(false)
		const user = inject("user")

		const ticketTypes = ref([])
		const ticketPriorities = ref([])
		const ticketStatuses = ref([])

		const ticketController = ref({})

		const contacts = ref([])
		const contactController = ref({})

		const agents = ref([])
		const agentGroups = ref([])
		const agentController = ref({})

		provide("ticketTypes", ticketTypes)
		provide("ticketPriorities", ticketPriorities)
		provide("ticketStatuses", ticketStatuses)

		provide("ticketController", ticketController)

		provide("contacts", contacts)
		provide("contactController", contactController)

		provide("agents", agents)
		provide("agentGroups", agentGroups)
		provide("agentController", agentController)

		return {
			mounted,
			user,

			ticketTypes,
			ticketPriorities,
			ticketStatuses,

			ticketController,

			contacts,
			contactController,

			agents,
			agentGroups,
			agentController,
		}
	},
	computed: {
		initialized() {
			if (!this.mounted) return false
			if (!this.user.isLoggedIn()) return false
			if (!this.user.has_desk_access) return false
			if (this.$resources.frappedeskSettings.loading) return false
			if (!this.$resources.frappedeskSettings.data.initial_agent_set) {
				this.$resources.setupInitialAgent.submit()
				return false
			}
			if (
				!this.$resources.frappedeskSettings.data
					.initial_demo_ticket_created
			) {
				this.$resources.createInitialDemoTicket.submit()
				return false
			}

			return true
		},
		defaultOutgoingEmailAccountSetup() {
			if (this.$resources.defaultOutgoingEmailAccount.loading) {
				return "NOT SET"
			}
			return this.$resources.defaultOutgoingEmailAccount.data > 0
		},
	},
	mounted() {
		if (!this.user.isLoggedIn()) {
			this.$router.push({
				name: "DeskLogin",
				query: { route: this.$route.path },
			})
			return
		}
		if (!this.user.has_desk_access) {
			this.$router.push({ path: "/support/tickets" })
			return
		}
		this.$resources.frappedeskSettings.fetch()
		this.ticketController.set = (ticketId, type, ref = null) => {
			switch (type) {
				case "type":
					return this.$resources.assignTicketType.submit({
						ticket_id: ticketId,
						type: ref,
					})
				case "status":
					return this.$resources.assignTicketStatus.submit({
						ticket_id: ticketId,
						status: ref,
					})
				case "priority":
					return this.$resources.assignTicketPriority.submit({
						ticket_id: ticketId,
						priority: ref,
					})
				case "contact":
					return this.$resources.updateTicketContact.submit({
						ticket_id: ticketId,
						contact: ref,
					})
				case "agent":
					return this.$resources.assignTicketToAgent.submit({
						ticket_id: ticketId,
						agent_id: ref,
					})
			}
		}
		this.ticketController.new = (type, values) => {
			switch (type) {
				case "ticket":
					return this.$resources.createTicket.submit({
						values,
					})
				case "type":
					this.$resources.createTicketType.submit({
						type: values,
					})
					break
			}
		}
		this.$socket.on("list_update", (data) => {
			switch (data.doctype) {
				case "Ticket Type":
					this.$resources.types.reload()
					break
				case "Agent":
					this.$resources.agents.reload()
					break
			}
		})

		this.mounted = true
	},
	unmounted() {
		this.$socket.off("list_update")
	},
	watch: {
		initialized(val) {
			if (val) {
				this.handlePostOnboardSetupReqs()
			}
		},
	},
	methods: {
		handlePostOnboardSetupReqs() {
			// helpdesk name
			if (
				!this.$resources.frappedeskSettings.data.helpdesk_name &&
				!this.$resources.frappedeskSettings.data
					.initial_helpdesk_name_setup_skipped
			) {
				this.showHelpdeskNameSetupToast()
				return
			}
			// default email account
			if (
				this.defaultOutgoingEmailAccountSetup != "NOT SET" &&
				!this.defaultOutgoingEmailAccountSetup
			) {
				this.showDefaultEmailAccountSetupToast()
				return
			}
			// add agents
			if (
				!this.$resources.agentCount.loading &&
				this.$resources.agentCount.data == 0
			) {
				// this block should theoretically never fire, since the initial agent is created during the setup process
				this.showAddAgentsToast()
			}
		},
		showHelpdeskNameSetupToast() {
			console.log("showing helpdesk name setup toast")
			this.$toast({
				title: "Setup Helpdesk Name",
				form: {
					inputs: [
						{
							type: "text",
							fieldname: "helpdesk_name",
							placeholder: "eg: FDESK",
						},
					],
					onSubmit: (values) => {
						if (values.helpdesk_name) {
							this.$resources.setHelpdeskName.submit({
								name: values.helpdesk_name,
							})
						}
					},
				},
				fixed: true,
				appearance: "info",
				position: "bottom-right",
				onClose: () => {
					this.$resources.skipHelpdeskNameSetup.submit()
				},
			})
		},
		showDefaultEmailAccountSetupToast() {
			this.$toast({
				title: "Default outgoing email account not added",
				text: "Please add a default outgoing email account in settings.",
				appearance: "info",
				icon: "info",
				iconClasses: "stroke-blue-500 stroke-2",
				fixed: true,
				position: "bottom-right",
				action: {
					title: "Setup now",
					onClick: () => {
						this.$clearToasts()
						this.$router.push({ name: "Emails" })
					},
				},
			})
		},
		showAddAgentsToast() {
			this.$toast({
				title: "Add agents",
				text: "Please add an agents from settings.",
				appearance: "info",
				icon: "info",
				iconClasses: "stroke-blue-500 stroke-2",
				fixed: true,
				position: "bottom-right",
				action: {
					title: "Add now",
					onClick: () => {
						this.$clearToasts()
						this.$router.push({ name: "Agents" })
					},
				},
			})
		},
	},
	resources: {
		// onboarding related resources
		// setters
		setupInitialAgent() {
			// sets up an initial agent
			return {
				method: "helpdesk.api.setup.initial_agent_setup",
				onSuccess: (res) => {
					this.$resources.frappedeskSettings.fetch()
				},
				onError: (err) => {
					this.$toast({
						title: "Something went wrong, while adding initial agent",
						text: "Please try again later.",
						customIcon: "circle-fail",
						appearance: "danger",
					})
				},
			}
		},
		createInitialDemoTicket() {
			// creates a demo ticket
			return {
				method: "helpdesk.api.setup.create_initial_demo_ticket",
				onSuccess: (res) => {
					this.$resources.frappedeskSettings.fetch()
				},
				onError: (err) => {
					this.$toast({
						title: "Something went wrong, while creating a demo ticket",
						text: "Please try again later.",
						customIcon: "circle-fail",
						appearance: "danger",
					})
				},
			}
		},
		setHelpdeskName() {
			// set helpdesk name in Helpdesk Settings
			return {
				method: "helpdesk.api.settings.update_helpdesk_name",
				onSuccess: (res) => {
					document.title = `Frappe Helpdesk ${res ? ` | ${res}` : ""}`
					this.$toast({
						title: "Helpdesk name updated!!",
						customIcon: "circle-check",
						appearance: "success",
					})
				},
				onError: (err) => {
					this.$toast({
						title: "Something went wrong, updating helpdesk name",
						text: "Please try again later.",
						customIcon: "circle-fail",
						appearance: "danger",
					})
				},
			}
		},
		skipHelpdeskNameSetup() {
			// sets the values of skip_helpdesk_name_setup to true inside Helpdesk Settings
			return {
				method: "helpdesk.api.settings.skip_helpdesk_name_setup",
			}
		},
		// getters
		frappedeskSettings() {
			return {
				method: "frappe.client.get",
				params: {
					doctype: "Helpdesk Settings",
					name: "Helpdesk Settings",
				},
				onError: (error) => {
					this.$toast({
						title: "Something went wrong.",
						text: "Please try again later.",
						customIcon: "circle-fail",
						appearance: "danger",
					})
				},
			}
		},
		defaultOutgoingEmailAccount() {
			return {
				method: "frappe.client.get_count",
				params: {
					doctype: "Email Account",
					filters: [
						["use_imap", "=", 1],
						["IMAP Folder", "append_to", "=", "Ticket"],
						["default_outgoing", "=", 1],
					],
				},
				auto: true,
			}
		},
		agentCount() {
			return {
				method: "frappe.client.get_count",
				params: {
					doctype: "Agent",
				},
				auto: true,
			}
		},

		// ticket related resources
		createTicket() {
			return {
				method: "helpdesk.api.ticket.create_new",
				onSuccess: () => {
					// TODO:
				},
				onError: () => {
					// TODO:
				},
			}
		},
		updateTicketContact() {
			return {
				method: "helpdesk.api.ticket.update_contact",
				onSuccess: async (ticket) => {
					// TODO:
				},
				onError: () => {
					// TODO:
				},
			}
		},
		types() {
			return {
				method: "frappe.client.get_list",
				params: {
					doctype: "Ticket Type",
					pluck: "name",
				},
				auto: this.user.has_desk_access,
				onSuccess: (data) => {
					this.ticketTypes = data
				},
				onError: () => {
					// TODO:
				},
			}
		},
		priorities() {
			return {
				method: "frappe.client.get_list",
				params: {
					doctype: "Ticket Priority",
				},
				auto: this.user.has_desk_access,
				onSuccess: (data) => {
					this.ticketPriorities = data
				},
				onError: () => {
					// TODO:
				},
			}
		},
		statuses() {
			return {
				method: "helpdesk.api.ticket.get_all_ticket_statuses",
				auto: this.user.has_desk_access,
				onSuccess: (data) => {
					this.ticketStatuses = data
				},
				onError: () => {
					// TODO:
				},
			}
		},
		contacts() {
			return {
				method: "frappe.client.get_list",
				params: {
					doctype: "Contact",
					fields: ["*"],
					limit_page_length: 0,
				},
				auto: this.user.has_desk_access,
				onSuccess: (data) => {
					this.contacts = data
				},
				onError: () => {
					// TODO:
				},
			}
		},
		agents() {
			return {
				method: "frappe.client.get_list",
				params: {
					doctype: "Agent",
					fields: [
						"name",
						"agent_name",
						"user.user_image as user_image",
					],
				},
				auto: this.user.has_desk_access,
				onSuccess: (data) => {
					this.agents = data
				},
				onError: () => {
					// TODO:
				},
			}
		},
		agentGroups() {
			return {
				method: "frappe.client.get_list",
				params: {
					doctype: "Agent Group",
				},
				auto: this.user.has_desk_access,
				onSuccess: (data) => {
					this.agentGroups = data
				},
				onError: () => {
					// TODO:
				},
			}
		},
		assignTicketToAgent() {
			return {
				method: "helpdesk.api.ticket.assign_ticket_to_agent",
				onSuccess: async () => {
					this.$event.emit("update_ticket_list")
				},
				onError: () => {
					// TODO:
				},
			}
		},
		assignTicketType() {
			return {
				method: "helpdesk.api.ticket.assign_ticket_type",
				onSuccess: async (ticket) => {},
				onError: () => {
					// TODO:
				},
			}
		},
		assignTicketStatus() {
			return {
				method: "helpdesk.api.ticket.assign_ticket_status",
				onSuccess: async () => {
					this.$event.emit("update_ticket_list")
				},
				onError: () => {
					// TODO:
				},
			}
		},
		assignTicketPriority() {
			return {
				method: "helpdesk.api.ticket.assign_ticket_priority",
				onSuccess: async (ticket) => {},
				onError: () => {
					// TODO:
				},
			}
		},
		createTicketType() {
			return {
				method: "helpdesk.api.ticket.check_and_create_ticket_type",
				onSuccess: () => {
					this.$resources.types.fetch()
				},
				onError: () => {
					// TODO:
				},
			}
		},
	},
	directivs: {},
}
</script>
