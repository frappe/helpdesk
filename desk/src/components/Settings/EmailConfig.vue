<template>
  <div class="px-10 py-8">
    <EmailAccounts
      doctype="HD Ticket"
      :is-v2-site="isV2Site"
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

const isV2Site = window.is_v2_site;
const { updateOnboardingStep } = useOnboarding("helpdesk") ?? {};

function onCreated(service: string) {
  updateOnboardingStep?.("setup_email_account");
  capture("email_account_created", { data: { service: service || "Custom" } });
}
</script>
