<template>
	<div class="flex flex-col gap-4">
		<component :is="steps[step]" />
	</div>
</template>

<script setup lang="ts">
import { onMounted } from "vue";
import { storeToRefs } from "pinia";
import { capture } from "@/telemetry";
import { useOnboardingEmailStore } from "./data";
import EmailIntro from "./EmailIntro.vue";
import SelectService from "./SelectService.vue";
import EmailCredentials from "./EmailCredentials.vue";
import SuccessMessage from "./SuccessMessage.vue";

const onboardingEmailStore = useOnboardingEmailStore();
const { step } = storeToRefs(onboardingEmailStore);
const steps = [EmailIntro, SelectService, EmailCredentials, SuccessMessage];

onMounted(() => capture("onboarding_email_reached"));
</script>
