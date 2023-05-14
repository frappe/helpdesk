<template>
	<div
		class="flex select-none flex-col border-r border-gray-200 bg-gray-50 p-2 text-base transition-all duration-300 ease-in-out"
		:class="{
			'w-56': sidebarStore.isExpanded,
			'w-12': !sidebarStore.isExpanded,
		}"
	>
		<UserMenu class="pb-2" :options="profileSettings" />
		<LinkGroup :options="menuOptions" />
		<div class="grow"></div>
		<LinkGroup :options="footerOptions" />
	</div>
</template>

<script setup lang="ts">
import { useRouter } from "vue-router";
import { useAuthStore } from "@/stores/auth";
import { useKeymapStore } from "@/stores/keymap";
import { useSidebarStore } from "@/stores/sidebar";
import { CUSTOMER_PORTAL_LANDING } from "@/router";
import UserMenu from "./UserMenu.vue";
import LinkGroup from "./LinkGroup.vue";
import IconDashboard from "~icons/espresso/dashboard";
import IconDashboardSolid from "~icons/espresso/dashboard-solid";
import IconTicket from "~icons/espresso/ticket";
import IconTicketSolid from "~icons/espresso/ticket-solid";
import IconCustomer from "~icons/espresso/customer";
import IconCustomerSolid from "~icons/espresso/customer-solid";
import IconContact from "~icons/espresso/contact";
import IconContactSolid from "~icons/espresso/contact-solid";
import IconKnowledgeBase from "~icons/espresso/knowledge-base";
import IconKnowledgeBaseSolid from "~icons/espresso/knowledge-base-solid";
import IconSettings from "~icons/espresso/settings";
import IconSettingsSolid from "~icons/espresso/settings-solid";

const router = useRouter();
const authStore = useAuthStore();
const keymapStore = useKeymapStore();
const sidebarStore = useSidebarStore();

const menuOptions = [
	{
		label: "Dashboard",
		icon: IconDashboard,
		iconActive: IconDashboardSolid,
		to: "DeskDashboard",
	},
	{
		label: "Tickets",
		icon: IconTicket,
		iconActive: IconTicketSolid,
		to: "DeskTickets",
	},
	{
		label: "Knowledge Base",
		icon: IconKnowledgeBase,
		iconActive: IconKnowledgeBaseSolid,
		to: "DeskKBHome",
	},
	{
		label: "Customers",
		icon: IconCustomer,
		iconActive: IconCustomerSolid,
		to: "Customers",
	},
	{
		label: "Contacts",
		icon: IconContact,
		iconActive: IconContactSolid,
		to: "Contacts",
	},
];

const footerOptions = [
	{
		label: "Settings",
		icon: IconSettings,
		iconActive: IconSettingsSolid,
		to: "Settings",
	},
];

const profileSettings = [
	{
		label: "Shortcuts",
		icon: "command",
		handler: () => keymapStore.toggleVisibility(true),
	},
	{
		label: "Customer portal",
		icon: "users",
		handler: () => {
			const path = router.resolve({ name: CUSTOMER_PORTAL_LANDING });
			window.open(path.href, "_blank");
		},
	},
	{
		label: "Log out",
		icon: "log-out",
		handler: () => authStore.logout(),
	},
];
</script>
