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
import { markPersonaCaptured } from "@/persona";
import { capture } from "@/telemetry";
import { __ } from "@/translation";
import { usePageMeta } from "frappe-ui";
import { ref } from "vue";
import { useRouter } from "vue-router";

const router = useRouter();
const leaving = ref(false);
const FADE_MS = 300;

async function finishOnboarding() {
  leaving.value = true;
  // Persist and fade in parallel; localStorage in markPersonaCaptured is the
  // durable guard, so a failed persist can be ignored here.
  const fade = new Promise((resolve) => setTimeout(resolve, FADE_MS));
  await Promise.allSettled([markPersonaCaptured(), fade]);
  router.push({ name: "Home" });
}

function submitPersona(answers: Record<string, string | string[]>) {
  capture("onboarding_persona", { data: answers });
  finishOnboarding();
}

const questions = [
  {
    key: "current_solution",
    title: __("What do you currently use to manage customer support?"),
    options: [
      { label: __("Spreadsheets"), value: "spreadsheets" },
      { label: __("Notion"), value: "notion" },
      { label: __("Zendesk"), value: "zendesk" },
      { label: __("Freshdesk"), value: "freshdesk" },
      { label: __("Intercom"), value: "intercom" },
      { label: __("Jira Service Management"), value: "jira" },
      { label: __("Zoho Desk"), value: "zoho_desk" },
      { label: __("Salesforce Service Cloud"), value: "salesforce" },
      { label: __("Other"), value: "other" },
      { label: __("We don't use any helpdesk yet"), value: "none" },
      {
        label: __("Shared email inbox (Gmail, Outlook, etc.)"),
        value: "shared_inbox",
      },
    ],
  },
  {
    key: "contact_channels",
    title: __("How do your customers currently contact your support team?"),
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
      {
        label: __("Keeping track of customer requests"),
        value: "tracking_requests",
      },
      { label: __("Missing or delayed responses"), value: "delayed_responses" },
      {
        label: __("Assigning tickets to the right agent"),
        value: "assignment",
      },
      { label: __("Other"), value: "other" },
    ],
  },
  {
    key: "first_goal",
    title: __("What would you like to do first in Frappe Helpdesk?"),
    options: [
      { label: __("Connect my support email"), value: "connect_email" },
      { label: __("Set up a customer portal"), value: "setup_portal" },
      { label: __("Create my first ticket"), value: "create_ticket" },
      { label: __("Invite my support team"), value: "invite_team" },
      { label: __("Explore the product first"), value: "explore" },
    ],
  },
];

usePageMeta(() => ({ title: __("Welcome to Frappe Helpdesk") }));
</script>
