<template>
	<Dialog v-model="isVisible" class="bg-gray-900" :options="options">
		<template #body-content>
			<div class="mt-4 text-base text-gray-900">
				<component :is="steps[step]['component']" />
			</div>
		</template>
	</Dialog>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";
import { Dialog } from "frappe-ui";
import SetupName from "./SetupName.vue";
import SetupLogo from "./SetupLogo.vue";
import SetupFavicon from "./SetupFavicon.vue";
import SetupSkipEmail from "./SetupSkipEmail.vue";
import SuccessMessage from "./SuccessMessage.vue";

const options = computed(() => ({
	title: steps[step.value]["title"],
	actions: [
		{
			label: "Next",
			appearance: "primary",
			class: "bg-gray-900 hover:bg-gray-800 text-sm",
			handler() {
				step.value++;
			},
			condition: step.value + 1 < steps.length,
		},
		{
			label: "Finish",
			appearance: "primary",
			class: "bg-gray-900 hover:bg-gray-800 text-sm",
			handler() {
				isVisible.value = false;
			},
			condition: step.value + 1 === steps.length,
		},
	].filter((a) => a.condition),
}));
const step = ref(0);
const steps = [
	{
		title: "Hello there! 👋",
		component: SetupName,
	},
	{
		title: "Let's set a logo 💫",
		component: SetupLogo,
	},
	{
		title: "How about a Favicon? 🌏",
		component: SetupFavicon,
	},
	{
		title: "Did you know? 💡",
		component: SetupSkipEmail,
	},
	{
		title: "That's it for now! 🙏",
		component: SuccessMessage,
	},
];

const isVisible = ref(true);
</script>
