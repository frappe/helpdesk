<template>
  <SidebarCard
    v-if="content"
    :theme="content.theme"
    :title="content.title"
    :description="content.description"
    :dismissible="content.dismissible"
    :action="{
      label: content.actionLabel,
      loading: opening,
      onClick: openBilling,
    }"
    @dismiss="dismiss"
  />
</template>

<script setup lang="ts">
import { useCloudSettings, useTrialCard } from "@/composables/cloudSettings";
import { __ } from "@/translation";
import type { BillingTrial } from "@frappe/cloud-sdk";
import { dayjsLocal, SidebarCard } from "frappe-ui";
import { computed } from "vue";

// From this many days left, the card turns amber
const URGENT_DAYS = 3;

const { trial, dismiss } = useTrialCard();
const { opening, openBilling } = useCloudSettings();

const content = computed(() => trial.value && trialCardContent(trial.value));

function trialCardContent(trial: BillingTrial): {
  theme: "gray" | "amber" | "red";
  title: string;
  description: string;
  actionLabel: string;
  dismissible: boolean;
} {
  if (trial.state === "Ended") {
    return {
      theme: "red",
      title: __("Your trial has ended"),
      description: trial.deletes_on
        ? __("Your site will be deleted on {0}. Choose a plan to keep it.", [
            dayjsLocal(trial.deletes_on).format("D MMM"),
          ])
        : __("Choose a plan to keep using your site."),
      actionLabel: __("Choose a plan"),
      dismissible: false,
    };
  }
  if (trial.held) {
    return {
      theme: "amber",
      title: __("Your plan is over your spending limit"),
      description: __(
        "Raise the limit or choose a smaller plan to end your trial."
      ),
      actionLabel: __("Manage billing"),
      dismissible: true,
    };
  }
  return {
    theme: trial.days_left <= URGENT_DAYS ? "amber" : "gray",
    title: endsInTitle(trial.days_left),
    description: __("Choose a plan to keep your site after the trial."),
    actionLabel: __("Choose a plan"),
    dismissible: true,
  };
}

function endsInTitle(daysLeft: number) {
  if (daysLeft <= 0) return __("Your trial ends today");
  if (daysLeft === 1) return __("Your trial ends tomorrow");
  return __("Your trial ends in {0} days", [String(daysLeft)]);
}
</script>
