<template>
  <div class="flex-1">
    <div v-if="step === 'email-add'" class="h-full">
      <EmailAccountSetup @update:step="updateStep" />
    </div>
    <div v-else-if="step === 'email-list'" class="h-full">
      <EmailAccountList @update:step="updateStep" />
    </div>
    <div v-else-if="step === 'email-edit'" class="h-full">
      <div>Email Edit</div>
      <div @click="updateStep('email-list')" class="cursor-pointer">abc</div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Ref, ref } from "vue";
import EmailAccountList from "./EmailAccountList.vue";
import EmailAccountSetup from "./EmailAccountSetup.vue";
import { EmailStep } from "@/types";

const step: Ref<EmailStep> = ref("email-list");
function updateStep(newStep: EmailStep) {
  step.value = newStep;
}
</script>

<style scoped></style>
