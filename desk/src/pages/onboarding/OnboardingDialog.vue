<template>
	<Dialog v-model="isVisible" :options="options">
		<template #body-content>
			<div class="mt-4 text-base text-gray-900">
				<component :is="steps[step]" />
			</div>
		</template>
	</Dialog>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { Dialog } from "frappe-ui";
import SetupName from "./SetupName.vue";
import SetupLogo from "./SetupLogo.vue";

const options = {
	title: "Hello there! 👋",
	actions: [
		{
			label: "Next",
			appearance: "primary",
			class: "bg-gray-900 hover:bg-gray-800 text-sm",
			handler() {
				step.value++;
			},
		},
	],
};
const step = ref(0);
const steps = [SetupName, SetupLogo];

const isVisible = ref(true);
</script>
