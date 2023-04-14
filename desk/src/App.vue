<template>
	<router-view />
	<Toasts />
</template>

<script setup lang="ts">
import { provide, ref, onMounted } from "vue";
import { createResource } from "frappe-ui";
import { createToast } from "@/utils/toasts";
import { Toasts } from "@/components/global/toast";

const viewportWidth = ref(
	Math.max(document.documentElement.clientWidth || 0, window.innerWidth || 0)
);

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
