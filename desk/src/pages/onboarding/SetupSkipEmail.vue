<template>
	<div class="flex flex-col gap-4 text-gray-800">
		{{ query }}
		<Button
			:label="isYes ? 'No' : 'Yes'"
			class="w-max bg-gray-900 text-white hover:bg-gray-800"
			@click="update(!isYes)"
		/>
	</div>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { createResource } from "frappe-ui";

const query =
	"Did you know that our Helpdesk is designed to function independently, \
	without relying on email? Our customer portal is finely tuned to be a \
	standalone solution, eliminating the hassle of email setup. Would you \
	like me to disable the email workflow for you?";
const isYes = ref(false);

const r = createResource({
	url: "frappe.client.set_value",
	debounce: 1000,
	onSuccess(data) {
		isYes.value = data.skip_email_workflow;
	},
});

function update(value: boolean) {
	r.submit({
		doctype: "HD Settings",
		name: "HD Settings",
		fieldname: "skip_email_workflow",
		value,
	});
}
</script>
