<template>
	<div class="flex flex-col items-center justify-center gap-4">
		<div class="text-7xl">
			{{ emoji }}
		</div>
		<div class="text-center text-base italic text-gray-900">
			{{ message }}
		</div>
	</div>
</template>

<script setup lang="ts">
import { onMounted } from "vue";
import { capture } from "@/telemetry";

const emoji = "✔️";
const message =
	"Fantastic! Your email is now active. You are ready unleash true \
	potential of Frappe Helpdesk!";

onMounted(() => capture("onboarding_email_finished"));
</script>
