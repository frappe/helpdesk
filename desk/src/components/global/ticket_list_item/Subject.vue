<template>
	<router-link
		:to="{
			path: `/tickets/${ticket.name}`,
		}"
		role="button"
		class="line-clamp-1 text-gray-600 hover:text-gray-900"
		:class="{
			'font-semibold text-gray-900': !(JSON.parse(ticket._seen) || []).includes(
				authStore.userId
			),
		}"
	>
		{{ ticket.subject }}
	</router-link>
</template>

<script setup lang="ts">
import { useAuthStore } from "@/stores/auth";

defineProps({
	ticket: {
		type: Object,
		required: true,
	},
});

const authStore = useAuthStore();
</script>
