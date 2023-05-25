<template>
	<div class="flex flex-col gap-4">
		<div>
			<div class="font-medium">Don't forget to star our GitHub repo</div>
			<a class="text-sm text-gray-800" :href="github" target="_blank">
				{{ github }}
			</a>
		</div>
		<div>
			<div class="font-medium">
				If you find any bugs, report them at the issue tracker
			</div>
			<a class="text-sm text-gray-800" :href="issues" target="_blank">
				{{ issues }}
			</a>
		</div>
		<div>
			<div class="font-medium">
				For any queries or support, reach out to our support portal
			</div>
			<a class="text-sm text-gray-800" :href="support" target="_blank">
				{{ support }}
			</a>
		</div>
		<div>
			<div class="font-medium">Or via our e-mail</div>
			<a class="text-sm text-gray-800" :href="'mailto:' + email">
				{{ email }}
			</a>
		</div>
	</div>
</template>

<script setup lang="ts">
import { onMounted } from "vue";
import { capture } from "@/telemetry";

const github = "https://github.com/frappe/helpdesk";
const issues = "https://github.com/frappe/helpdesk/issues";
const support = "https://frappedesk.com/helpdesk";
const email = "hello@frappe.io";

onMounted(() => capture("onboarding_finished"));
</script>
