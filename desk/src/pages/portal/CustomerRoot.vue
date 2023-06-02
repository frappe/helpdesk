<template>
	<div class="min-h-screen bg-gray-100">
		<div
			class="mx-auto py-4"
			:style="{
				width: '900px',
			}"
		>
			<div class="mb-4 flex items-center justify-between text-base">
				<RouterLink :to="{ name: CUSTOMER_PORTAL_LANDING }">
					<img
						v-if="configStore.brandLogo"
						:src="configStore.brandLogo"
						class="h-7"
					/>
					<div v-else class="text-6xl text-gray-800">
						{{ configStore.helpdeskName }}
					</div>
				</RouterLink>
				<Dropdown :options="options">
					<template #default="{ open }">
						<div
							class="flex cursor-pointer items-center gap-2 rounded-lg text-base text-gray-900"
						>
							<Avatar
								size="sm"
								:image-u-r-l="authStore.userImage"
								:label="authStore.userName"
							/>
							{{ authStore.userName }}
							<div class="text-gray-700">
								<IconCaretUp v-if="open" />
								<IconCaretDown v-else />
							</div>
						</div>
					</template>
				</Dropdown>
			</div>
			<div
				class="rounded-lg bg-white"
				:style="{
					'box-shadow':
						'0px 0px 1px rgba(0, 0, 0, 0.45), 0px 1px 2px rgba(0, 0, 0, 0.1)',
				}"
			>
				<RouterView />
			</div>
		</div>
	</div>
</template>

<script setup lang="ts">
import { useRouter } from "vue-router";
import { Avatar, Dropdown } from "frappe-ui";
import { useAuthStore } from "@/stores/auth";
import { useConfigStore } from "@/stores/config";
import { CUSTOMER_PORTAL_LANDING, KB_PUBLIC } from "@/router";
import IconCaretDown from "~icons/ph/caret-down";
import IconCaretUp from "~icons/ph/caret-up";

const router = useRouter();
const authStore = useAuthStore();
const configStore = useConfigStore();

const options = [
	{
		label: "Knowledge Base",
		icon: "book-open",
		handler: () => {
			const path = router.resolve({ name: KB_PUBLIC });
			window.open(path.href, "_blank");
		},
	},
	{
		label: "My Account",
		icon: "user",
		handler: () => {
			const protocol = window.location.protocol;
			const domain = window.location.hostname;
			const path = protocol + "//" + domain + "/me";
			window.open(path, "_blank");
		},
	},
	{
		label: "Log out",
		icon: "log-out",
		handler: () => authStore.logout(),
	},
];
</script>
