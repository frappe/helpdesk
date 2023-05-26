<template>
	<div class="flex flex-col gap-4 text-gray-800">
		{{ text }}
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
		<div class="italic text-gray-800">
			{{ subText }}
		</div>
	</div>
</template>

<script setup lang="ts">
import { onMounted, ref } from "vue";
import { createResource } from "frappe-ui";
import { capture } from "@/telemetry";
import IconCheck from "~icons/ph/check-bold";

const text =
	"Now, let's set a name for your Helpdesk that reflects your organization's \
	identity and values. So, what would you like to name your Helpdesk?";
const subText =
	"Choose a name that resonates with your brand and instills \
	trust in your customers";
const placeholder = "My Helpdesk";
const isCheckVisible = ref(false);

const r = createResource({
	url: "frappe.client.set_value",
	debounce: 1000,
	onSuccess() {
		isCheckVisible.value = true;
		capture("onboarding_name_changed");
	},
});

function update(value: string) {
	isCheckVisible.value = false;
	r.submit({
		doctype: "HD Settings",
		name: "HD Settings",
		fieldname: "helpdesk_name",
		value,
	});
}

onMounted(() => capture("onboarding_name_reached"));
</script>
