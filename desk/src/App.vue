<template>
	<router-view />
	<Toasts />
	<KeymapDialog />
</template>

<script setup lang="ts">
import { provide, ref, onMounted } from "vue";
import { createToast } from "@/utils/toasts";
import KeymapDialog from "@/pages/KeymapDialog.vue";
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
</script>
