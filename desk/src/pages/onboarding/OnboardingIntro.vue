<template>
	<div class="flex flex-col gap-2 text-gray-800">
		<div class="text-base text-gray-900">
			{{ text }}
		</div>
		<div class="text-base text-gray-900">
			{{ subText }}
		</div>
	</div>
</template>

<script setup lang="ts">
import { onMounted } from "vue";
import { capture } from "@/telemetry";

const text =
	"We're excited to have you join us and explore the world of efficient customer support. \
	We are here to revolutionize the way you handle customer inquiries, streamline ticket \
	management, and deliver outstanding service.";
const subText =
	"Once again, welcome to Frappe Helpdesk! Let's hope for a long and smooth journey!";

onMounted(() => capture("onboarding_started"));
</script>
