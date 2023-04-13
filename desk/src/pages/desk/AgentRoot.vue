<template>
	<div v-if="initialized">
		<div class="flex h-screen w-screen flex-row">
			<SideBar />
			<router-view :key="$route.fullPath" class="z-0 grow" />
		</div>
	</div>
</template>

<script>
import { ref } from "vue";
import { useAuthStore } from "@/stores/auth";
import { CUSTOMER_PORTAL_LANDING } from "@/router";
import SideBar from "@/components/desk/sidebar/SideBar.vue";

export default {
	name: "AgentRoot",
	components: {
		SideBar,
	},
	setup() {
		const authStore = useAuthStore();
		const mounted = ref(false);

		return {
			authStore,
			mounted,
		};
	},
	computed: {
		initialized() {
			if (!this.mounted) return false;
			if (this.$resources.helpdeskSettings.loading) return false;

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
		if (!this.authStore.hasDeskAccess) {
			this.$router.replace({ name: CUSTOMER_PORTAL_LANDING });
			return;
		}

		this.$resources.helpdeskSettings.fetch();
		this.mounted = true;
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
			}
			// default email account
			if (
				!this.$resources.helpdeskSettings.data.suppress_default_email_toast &&
				this.defaultOutgoingEmailAccountSetup != "NOT SET" &&
				!this.defaultOutgoingEmailAccountSetup
			) {
				this.showDefaultEmailAccountSetupToast();
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
				title: "You don't have any agents",
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
	},
};
</script>
