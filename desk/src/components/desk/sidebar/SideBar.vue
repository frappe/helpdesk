<template>
	<div
		class="flex select-none flex-col border-r p-2 text-base transition-all duration-300 ease-in-out"
		:class="{
			'w-56': sidebarStore.isExpanded,
			'w-12': !sidebarStore.isExpanded,
		}"
	>
		<UserMenu class="pb-2" :options="profileSettings" />
		<LinkGroup :options="menuOptions" />
		<div class="grow"></div>
		<LinkGroup :options="footerOptions" />
		<Dialog
			v-model="showKeyboardShortcuts"
			:options="{ title: 'Keyboard Shortcuts' }"
		>
			<template #body-content>
				<div class="py-5 text-base">
					<table class="w-full table-fixed border-collapse border">
						<tbody>
							<tr
								v-for="shortcut in keyboardShortcuts"
								:key="shortcut.label"
								class="h-16 border-y"
							>
								<td class="w-28 border-r px-4">
									<span
										class="rounded bg-gray-100 p-1.5 text-gray-500 shadow shadow-gray-400"
									>
										{{ shortcut.sequence }}
									</span>
								</td>
								<td class="px-4">{{ shortcut.label }}</td>
							</tr>
						</tbody>
					</table>
				</div>
			</template>
		</Dialog>
	</div>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { useAuthStore } from "@/stores/auth";
import { useSidebarStore } from "@/stores/sidebar";
import UserMenu from "./UserMenu.vue";
import LinkGroup from "./LinkGroup.vue";
import IconDashboard from "@/assets/icons/dashboard.svg?component";
import IconDashboardSolid from "@/assets/icons/dashboard-solid.svg?component";
import IconTicket from "@/assets/icons/ticket.svg?component";
import IconTicketSolid from "@/assets/icons/ticket-solid.svg?component";
import IconCustomer from "@/assets/icons/customer.svg?component";
import IconCustomerSolid from "@/assets/icons/customer-solid.svg?component";
import IconContact from "@/assets/icons/contact.svg?component";
import IconContactSolid from "@/assets/icons/contact-solid.svg?component";
import IconKnowledgeBase from "@/assets/icons/knowledge-base.svg?component";
import IconKnowledgeBaseSolid from "@/assets/icons/knowledge-base-solid.svg?component";
import IconSettings from "@/assets/icons/settings.svg?component";
import IconSettingsSolid from "@/assets/icons/settings-solid.svg?component";

const authStore = useAuthStore();
const sidebarStore = useSidebarStore();
const isMac = navigator.userAgent.indexOf("Mac OS X") != -1;
const showKeyboardShortcuts = ref(false);

const keyboardShortcuts = [
	{
		sequence: isMac ? "⌃ + ⌥ + R" : "Ctrl + Alt + R",
		label: "Mark status of ticket as Replied",
	},
	{
		sequence: isMac ? "⌃ + ⌥ + E" : "Ctrl + Alt + E",
		label: "Mark status of ticket as Resolved",
	},
	{
		sequence: isMac ? "⌃ + ⌥ + C" : "Ctrl + Alt + C",
		label: "Mark status of ticket as Closed",
	},
];

const menuOptions = [
	{
		label: "Dashboard",
		icon: IconDashboard,
		iconActive: IconDashboardSolid,
		to: "Dashboard",
	},
	{
		label: "Tickets",
		icon: IconTicket,
		iconActive: IconTicketSolid,
		to: "DeskTickets",
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
		label: "Knowledge Base",
		icon: IconKnowledgeBase,
		iconActive: IconKnowledgeBaseSolid,
		to: "DeskKBHome",
	},
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
		handler: () => {
			showKeyboardShortcuts.value = true;
		},
	},
	{
		label: "Customer portal",
		icon: "users",
		handler: () => {
			window.open("/my-tickets", "_blank");
		},
	},
	{
		label: "Log out",
		icon: "log-out",
		handler: () => authStore.logout(),
	},
];
</script>
