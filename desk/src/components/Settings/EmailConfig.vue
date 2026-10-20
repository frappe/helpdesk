<template>
  <div class="px-10 py-8">
    <EmailAccounts
      doctype="HD Ticket"
      v-model:dirty="disableSettingModalOutsideClick"
      @created="onCreated"
    />
  </div>
</template>

<script setup lang="ts">
import { useOnboarding } from "@framework/ui";
import { EmailAccounts } from "@framework/ui/EmailAccounts";
import { capture } from "@/telemetry";
import { disableSettingModalOutsideClick } from "./settingsModal";

const { updateOnboardingStep } = useOnboarding("helpdesk") ?? {};

function onCreated(service: string) {
  updateOnboardingStep?.("setup_email_account");
  capture("email_account_created", { data: { service: service || "Custom" } });
}
</script>
