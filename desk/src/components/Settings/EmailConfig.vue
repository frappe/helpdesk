<template>
  <div v-if="step === 'email-add'" class="h-full">
    <EmailAdd @update:step="updateStep" />
  </div>
  <div v-else-if="step === 'email-provider-setup'" class="h-full">
    <EmailProviderSetup
      :service="selectedService"
      :back-step="backStep"
      @update:step="updateStep"
    />
  </div>
  <div v-else-if="step === 'email-custom-setup'" class="h-full">
    <EmailCustomMailSetup :back-step="backStep" @update:step="updateStep" />
  </div>
  <div v-else-if="step === 'email-list'" class="h-full">
    <EmailAccountList @update:step="updateStep" />
  </div>
  <div v-else-if="step === 'email-edit'" class="h-full">
    <EmailCustomMailEdit
      v-if="isCustomAccount"
      :account-data="accountData"
      @update:step="updateStep"
    />
    <EmailEdit v-else :account-data="accountData" @update:step="updateStep" />
  </div>
</template>

<script setup lang="ts">
import { computed, onUnmounted, provide, Ref, ref } from "vue";
import { createListResource } from "frappe-ui";
import EmailAdd from "./EmailAdd.vue";
import EmailProviderSetup from "./EmailProviderSetup.vue";
import EmailCustomMailSetup from "./EmailCustomMailSetup.vue";
import EmailAccountList from "./EmailAccountList.vue";
import EmailEdit from "./EmailEdit.vue";
import EmailCustomMailEdit from "./EmailCustomMailEdit.vue";
import {
  EmailAccount,
  EmailAccountListResourceSymbol,
  EmailStep,
} from "@/types";

const step: Ref<EmailStep> = ref("email-list");
const accountData: Ref<EmailAccount | null> = ref(null);
const selectedService = ref<string>("");
const backStep: Ref<EmailStep> = ref("email-list");

const emailAccounts = createListResource({
  doctype: "Email Account",
  cache: ["Email Accounts"],
  fields: ["*"],
  filters: { email_id: ["Not Like", "%example%"] },
  orderBy: "creation desc",
  pageLength: 50,
  auto: true,
});

provide(EmailAccountListResourceSymbol, emailAccounts);

const isCustomAccount = computed(() => {
  const account = accountData.value;
  if (!account) return false;
  if (account.service === "Custom") return true;
  if (!account.service && (account.email_server || account.smtp_server))
    return true;
  return false;
});

function updateStep(
  newStep: EmailStep,
  data?: EmailAccount | { service?: string }
) {
  if (newStep === "email-provider-setup" || newStep === "email-custom-setup") {
    backStep.value = step.value === "email-add" ? "email-add" : "email-list";
  }
  step.value = newStep;
  if (newStep === "email-provider-setup") {
    selectedService.value = (data as { service?: string })?.service || "";
    accountData.value = null;
    return;
  }
  if (newStep === "email-edit") {
    accountData.value = data as EmailAccount;
    selectedService.value = "";
    return;
  }
  accountData.value = null;
  selectedService.value = "";
  if (newStep === "email-list") emailAccounts.reload();
}

onUnmounted(() => {
  emailAccounts.filters = {};
});
</script>
