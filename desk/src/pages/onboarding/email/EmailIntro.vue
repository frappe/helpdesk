<template>
	<div class="flex flex-col gap-4">
		<div class="text-gray-700">
			{{ help }}
		</div>
		<Button
			label="Let's go!"
			appearance="primary"
			class="w-max bg-gray-900 text-white hover:bg-gray-800"
			@click="next"
		/>
	</div>
</template>

<script setup lang="ts">
import { Button } from "frappe-ui";
import { useOnboardingEmailStore } from "./data";

const { next } = useOnboardingEmailStore();
const help =
	"Helpdesk is super powerful with an email. You can send and receive \
	mails from your inbox. Do you want to add an email now?";
</script>
