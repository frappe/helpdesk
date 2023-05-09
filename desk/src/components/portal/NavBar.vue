<template>
	<div
		class="container mx-auto flex flex-wrap items-center justify-between py-4"
	>
		<a href="/">
			<img
				v-if="configStore.brandLogo"
				:src="configStore.brandLogo"
				class="m-auto h-6"
			/>
			<div v-else class="text-gray-800">
				{{ configStore.helpdeskName }}
			</div>
		</a>
		<div class="flex items-center gap-4 text-lg text-gray-800">
			<div v-for="item in navbarItems" :key="item.label">
				<router-link :to="{ name: item.route }">
					<div class="hover:text-blue-600">{{ item.label }}</div>
				</router-link>
			</div>
			<Dropdown :options="profileItems">
				<template #default>
					<Avatar
						v-if="authStore.userId"
						:label="authStore.username"
						class="cursor-pointer"
						size="md"
						:image-u-r-l="authStore.userImage"
					/>
				</template>
			</Dropdown>
		</div>
	</div>
</template>

<script setup lang="ts">
import { Avatar, Dropdown } from "frappe-ui";
import { useAuthStore } from "@/stores/auth";
import { useConfigStore } from "@/stores/config";
import { CUSTOMER_PORTAL_NEW_TICKET, KNOWLEDGE_BASE_PUBLIC } from "@/router";

const authStore = useAuthStore();
const configStore = useConfigStore();

const profileItems = [
	{
		label: "My Account",
		handler: () => {
			window.open("/me");
		},
	},
	{
		label: "Logout",
		handler: () => {
			authStore.logout();
		},
	},
];

const navbarItems = [
	{
		label: "New Ticket",
		route: CUSTOMER_PORTAL_NEW_TICKET,
	},
	{
		label: "Knowledge Base",
		route: KNOWLEDGE_BASE_PUBLIC,
	},
];
</script>
