<template>
	<div class="flex flex-col gap-2 text-gray-800">
		{{ query }}
		<div class="relative flex items-center justify-end">
			<Input
				type="text"
				class="w-full"
				:placeholder="placeholder"
				@input="update"
			/>
			<IconCheck
				v-if="isCheckVisible"
				class="absolute mr-2 w-6 text-green-500"
			/>
		</div>
	</div>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { createResource } from "frappe-ui";
import IconCheck from "~icons/ph/check";

const r = createResource({
	url: "frappe.client.set_value",
	debounce: 1000,
	onSuccess() {
		isCheckVisible.value = true;
	},
});

const query = "What should we call your Helpdesk?";
const placeholder = "My Helpdesk";
const isCheckVisible = ref(false);

function update(value: string) {
	isCheckVisible.value = false;
	r.submit({
		doctype: "HD Settings",
		name: "HD Settings",
		fieldname: "helpdesk_name",
		value,
	});
}
</script>
