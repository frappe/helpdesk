<template>
	<div v-if="authStore.isLoggedIn">
		<router-view />
		<Toasts />
	</div>
	<div v-else class="flex h-full w-full max-w-full grow-0">
		<div class="m-auto text-base font-normal">
			<CustomIcons name="frappedesk" class="w-[200px]" />
		</div>
	</div>
</template>

<script setup lang="ts">
import { provide, ref, onMounted } from "vue";
import { createResource } from "frappe-ui";
import { useAuthStore } from "./stores/auth";
import { createToast } from "@/utils/toasts";
import { Toasts } from "@/components/global/toast";

const authStore = useAuthStore();
const viewportWidth = ref(
	Math.max(document.documentElement.clientWidth || 0, window.innerWidth || 0)
);

authStore.init();
provide("viewportWidth", viewportWidth);

onMounted(async () => {
	window.addEventListener("online", () => {
		createToast({
			title: "You are now online",
			icon: "wifi",
			iconClasses: "stroke-green-600",
		});
	});

	window.addEventListener("offline", () => {
		createToast({
			title: "You are now offline",
			icon: "wifi-off",
			iconClasses: "stroke-red-600",
		});
	});
});

createResource({
	url: "helpdesk.api.website.helpdesk_name",
	cache: true,
	auto: true,
	onSuccess: (res: string) => {
		document.title = `Helpdesk ${res ? ` | ${res}` : ""}`;
	},
});
</script>
