<template>
	<div
		class="flex w-56 shrink select-none flex-col border-r text-base text-gray-700"
	>
		<div>
			<Dropdown :options="profileSettings">
				<template #default="{ open }">
					<Button class="my-3 w-full bg-white px-2 hover:bg-white">
						<div class="flex items-center gap-2">
							<div>
								<Avatar
									size="sm"
									:label="authStore.userName"
									:image-u-r-l="authStore.userImage"
								/>
							</div>
							<div>
								{{ authStore.userName }}
							</div>
							<div>
								<FeatherIcon
									:name="open ? 'chevron-up' : 'chevron-down'"
									class="h-5 w-5 text-gray-500"
								/>
							</div>
						</div>
					</Button>
				</template>
			</Dropdown>
		</div>
		<div class="flex flex-col gap-1 px-2">
			<div
				v-for="option in menuOptions"
				:key="option.label"
				class="flex cursor-pointer items-center gap-2 rounded-lg p-2"
				:class="{
					'bg-gray-200': isActive(option.label),
					'text-gray-900': isActive(option.label),
					'hover:bg-gray-100': !isActive(option.label),
				}"
				@click="$router.push(option.to)"
			>
				<CustomIcons :name="option.icon" class="h-4 w-4" />
				<div>
					{{ option.label }}
				</div>
			</div>
		</div>
		<div class="grow"></div>
		<div class="mb-3 flex flex-col gap-1 px-2">
			<div
				v-for="option in footerOptions"
				:key="option.label"
				class="flex cursor-pointer items-center gap-2 rounded-lg p-2"
				:class="{
					'bg-gray-200': isActive(option.label),
					'text-gray-900': isActive(option.label),
					'hover:bg-gray-100': !isActive(option.label),
				}"
				@click="$router.push(option.to)"
			>
				<CustomIcons :name="option.icon" class="h-4 w-4" />
				<div>
					{{ option.label }}
				</div>
			</div>
		</div>
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
import { useRoute } from "vue-router";
import { Dropdown, FeatherIcon, Avatar } from "frappe-ui";
import CustomIcons from "@/components/desk/global/CustomIcons.vue";
import { useAuthStore } from "@/stores/auth";

const route = useRoute();
const authStore = useAuthStore();
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
		icon: "dashboard",
		to: {
			path: "/frappedesk/dashboard",
		},
	},
	{
		label: "Tickets",
		icon: "ticket",
		to: {
			path: "/frappedesk/tickets",
		},
	},
	{
		label: "Customers",
		icon: "customer",
		to: {
			path: "/frappedesk/customers",
		},
	},
	{
		label: "Contacts",
		icon: "customers",
		to: {
			path: "/frappedesk/contacts",
		},
	},
];

const footerOptions = [
	{
		label: "Knowledge Base",
		icon: "kb-articles",
		to: {
			path: "/frappedesk/kb",
		},
	},
	{
		label: "Settings",
		icon: "settings",
		to: {
			path: "/frappedesk/settings",
		},
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
			window.open("/support/tickets", "_blank");
		},
	},
	{
		label: "Log out",
		icon: "log-out",
		handler: () => authStore.logout(),
	},
];

const routeMap = {
	"Knowledge Base": "frappedesk/kb",
	Contacts: "frappedesk/contacts",
	Customers: "frappedesk/customers",
	Dashboard: "frappedesk/dashboard",
	Reports: "frappedesk/reports",
	Settings: "frappedesk/settings",
	Tickets: "frappedesk/tickets",
};

function isActive(label: string) {
	return route.path.includes(routeMap[label]);
}
</script>
