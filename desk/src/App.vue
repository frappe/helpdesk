<template>
	<div>
		<router-view />
		<Toasts />
	</div>
</template>

<script>
import { provide, ref } from "vue";
import { Toasts } from "@/components/global/toast";
import { useAuthStore } from "./stores/auth";

export default {
	name: "App",
	components: {
		Toasts,
	},
	setup() {
		const authStore = useAuthStore();
		const viewportWidth = ref(
			Math.max(
				document.documentElement.clientWidth || 0,
				window.innerWidth || 0
			)
		);

		authStore.init();

		provide("viewportWidth", viewportWidth);
	},
	mounted() {
		window.addEventListener("online", () => {
			this.$toast({
				title: "You're online now",
				icon: "wifi",
				iconClasses: "stroke-green-600",
			});
		});

		window.addEventListener("offline", () => {
			this.$toast({
				title: "You're offline now",
				icon: "wifi-off",
				iconClasses: "stroke-red-600",
			});
		});
	},
	resources: {
		helpdeskName() {
			return {
				url: "helpdesk.api.website.helpdesk_name",
				auto: true,
				onSuccess: (res) => {
					document.title = `Helpdesk ${res ? ` | ${res}` : ""}`;
				},
			};
		},
	},
};
</script>
