<template>
  <div
    class="relative flex min-h-screen flex-col overflow-y-auto bg-surface-gray-1 transition-opacity duration-300 ease-out"
    :class="leaving ? 'opacity-0' : 'opacity-100'"
  >
    <div class="flex flex-1 flex-col justify-start pb-8 pt-24">
      <Questionnaire
        class="h-full"
        :questions="questions"
        @submit="submitPersona"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import Questionnaire from "@/components/Questionnaire.vue";
import type { Question } from "@/components/Questionnaire.types";
import {
  setActiveSettingsTab,
  showSettingsModal,
} from "@/components/Settings/settingsModal";
import { markPersonaCaptured } from "@/persona";
import { capture } from "@/telemetry";
import { __ } from "@/translation";
import { usePageMeta } from "frappe-ui";
import { ref } from "vue";
import { useRouter } from "vue-router";

const router = useRouter();
const leaving = ref(false);
const FADE_MS = 300;

// The last question's "first goal" answer maps to a settings tab; other goals
// route directly (create ticket) or fall through to Home.
const settingsTabForGoal: Record<
  string,
  "Email Accounts" | "Invite Agents" | "General"
> = {
  connect_email: "Email Accounts",
  invite_team: "Invite Agents",
  setup_portal: "General",
};

async function finishOnboarding(answers: Record<string, string | string[]>) {
  leaving.value = true;
  // Persist and fade in parallel; localStorage is the durable guard.
  const brandName =
    typeof answers.company_name === "string" ? answers.company_name : undefined;
  const fade = new Promise((resolve) => setTimeout(resolve, FADE_MS));
  await Promise.allSettled([markPersonaCaptured(brandName), fade]);
  try {
    await routeToGoal(answers.first_goal);
  } catch {
    leaving.value = false; // navigation failed — un-fade so we're not stuck
  }
}

// Send the admin to their first goal: new ticket, a settings tab over Home, or Home.
async function routeToGoal(goal?: string | string[]) {
  if (goal === "create_ticket") {
    await router.push({ name: "TicketAgentNew" });
    return;
  }
  await router.push({ name: "Home" });
  const tab = typeof goal === "string" ? settingsTabForGoal[goal] : undefined;
  if (tab) {
    setActiveSettingsTab(tab);
    showSettingsModal.value = true;
  }
}

async function submitPersona(answers: Record<string, string | string[]>) {
  capture("onboarding_persona_hd", { data: answers });
  await finishOnboarding(answers);
}

const questions = [
  {
    key: "company_name",
    title: __("Tell us about your organization"),
    type: "text",
    label: __("What is your organization's name?"),
    placeholder: __("e.g. Acme Inc."),
    required: true,
    requiredMessage: __("Please enter your organization's name"),
    dropdown: {
      key: "company_size",
      label: __("How big is your support team?"),
      placeholder: __("Select team size"),
      options: [
        { label: __("1–5"), value: "1-5" },
        { label: __("6–10"), value: "6-10" },
        { label: __("11–25"), value: "11-25" },
        { label: __("26–50"), value: "26-50" },
        { label: __("51–100"), value: "51-100" },
        { label: __("100+"), value: "100+" },
      ],
    },
  },
  {
    key: "current_solution",
    title: __("What do you currently use to manage customer support?"),
    type: "choice",
    options: [
      { label: __("Spreadsheets"), value: "spreadsheets" },
      { label: __("Notion"), value: "notion" },
      { label: __("Zendesk"), value: "zendesk" },
      { label: __("Freshdesk"), value: "freshdesk" },
      { label: __("Intercom"), value: "intercom" },
      { label: __("Jira Service Management"), value: "jira" },
      { label: __("Zoho Desk"), value: "zoho_desk" },
      { label: __("Salesforce Service Cloud"), value: "salesforce" },
      { label: __("We don't use any helpdesk yet"), value: "none" },
      {
        label: __("Shared email inbox (Gmail, Outlook, etc.)"),
        value: "shared_inbox",
      },
      { label: __("Other"), value: "other" },
    ],
  },
  {
    key: "contact_channels",
    title: __("How do your customers currently contact your support team?"),
    type: "choice",
    multiple: true,
    options: [
      { label: __("Email"), value: "email" },
      { label: __("Support portal"), value: "support_portal" },
      { label: __("WhatsApp"), value: "whatsapp" },
      { label: __("Phone calls"), value: "phone_calls" },
      { label: __("Live chat"), value: "live_chat" },
      { label: __("Web form"), value: "web_form" },
      { label: __("Social media"), value: "social_media" },
      { label: __("In person"), value: "in_person" },
      { label: __("Other"), value: "other" },
    ],
  },
  {
    key: "preferred_channels",
    title: __(
      "How would you like your customers to create support tickets in Frappe Helpdesk?"
    ),
    type: "choice",
    multiple: true,
    options: [
      { label: __("Via email"), value: "email" },
      { label: __("Through a support portal"), value: "support_portal" },
      { label: __("Via WhatsApp"), value: "whatsapp" },
      { label: __("Live chat"), value: "live_chat" },
      { label: __("I'm not sure yet"), value: "not_sure" },
    ],
  },
  {
    key: "biggest_challenges",
    title: __("What's your biggest support challenge today?"),
    type: "choice",
    multiple: true,
    options: [
      {
        label: __("Managing customer conversations across channels"),
        value: "omnichannel",
      },
      {
        label: __("Finding past conversations"),
        value: "finding_conversations",
      },
      {
        label: __("Measuring team performance"),
        value: "measuring_performance",
      },
      { label: __("Scaling support as we grow"), value: "scaling" },
      { label: __("Missing or delayed responses"), value: "delayed_responses" },
      {
        label: __("Keeping track of customer requests"),
        value: "tracking_requests",
      },
      {
        label: __("Assigning tickets"),
        value: "assignment",
      },
      { label: __("Other"), value: "other" },
    ],
  },
  {
    key: "referral_source",
    title: __("How did you hear about Frappe Helpdesk?"),
    type: "text",
    multiline: true,
    placeholder: __("e.g. a friend, a search, or the Frappe community"),
  },
  {
    key: "first_goal",
    title: __("What would you like to do first in Frappe Helpdesk?"),
    type: "choice",
    options: [
      { label: __("Connect my support email"), value: "connect_email" },
      { label: __("Set up a customer portal"), value: "setup_portal" },
      { label: __("Create my first ticket"), value: "create_ticket" },
      { label: __("Invite my support team"), value: "invite_team" },
      { label: __("Explore the product first"), value: "explore" },
    ],
  },
] satisfies Question[];

usePageMeta(() => ({ title: __("Welcome to Frappe Helpdesk") }));
</script>
