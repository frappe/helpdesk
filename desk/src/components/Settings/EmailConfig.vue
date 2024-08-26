<template>
  <div class="flex-1">
    <div v-if="step === 'email-add'" class="h-full">
      <EmailAdd @update:step="updateStep" />
    </div>
    <div v-else-if="step === 'email-list'" class="h-full">
      <EmailAccountList @update:step="updateStep" />
    </div>
    <div v-else-if="step === 'email-edit'" class="h-full">
      <EmailEdit :account-data="accountData" @update:step="updateStep" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { Ref, ref } from "vue";
import EmailAdd from "./EmailAdd.vue";
import EmailAccountList from "./EmailAccountList.vue";
import EmailEdit from "./EmailEdit.vue";
import { EmailAccount, EmailStep } from "@/types";

const step: Ref<EmailStep> = ref("email-list");
const accountData: Ref<EmailAccount> = ref(null);
function updateStep(newStep: EmailStep, data?: EmailAccount) {
  step.value = newStep;
  accountData.value = data;
}
</script>
