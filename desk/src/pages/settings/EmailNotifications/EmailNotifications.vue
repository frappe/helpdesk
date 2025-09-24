<template>
  <SettingsHeader :routes="routes" />
  <div class="max-w-3xl xl:max-w-4xl mx-auto w-full p-4 lg:py-8">
    <SettingsLayoutHeader
      :title="__('Email Notifications')"
      :description="
        __(
          'Customize your email notification preferences to stay informed about important updates and activities.'
        )
      "
    />
    <div>
      <ul class="mt-8 pb-8 isolate flex flex-col gap-5.5">
        <li
          v-for="notification in notifications"
          :key="notification.name"
          class="flex items-center justify-between rounded relative"
        >
          <div class="flex flex-col gap-1 w-[90%]">
            <h2
              class="text-base font-medium text-ink-gray-7 relative z-10 pointer-events-none"
            >
              {{ notification.label }}
            </h2>
            <span
              class="text-sm text-ink-gray-5 truncate relative z-10 pointer-events-none whitespace-nowrap text-nowrap overflow-hidden overflow-ellipsis"
            >
              {{ notification.description }}
            </span>
          </div>
          <FeatherIcon
            name="chevron-right"
            class="text-ink-gray-7 size-4 relative z-10 pointer-events-none"
          />
          <button
            type="button"
            class="w-full h-full absolute -top-2.5 -left-2.5 hover:bg-gray-50 rounded-[inherit]"
            @click="router.push(notification.route)"
            :style="{
              width: 'calc(100% + 20px)',
              height: 'calc(100% + 20px)',
            }"
          >
            <span class="sr-only">{{
              __("customize {0}", notification.name)
            }}</span>
          </button>
        </li>
      </ul>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";
import SettingsHeader from "../components/SettingsHeader.vue";
import { __ } from "@/translation";
import { useRouter } from "vue-router";
import SettingsLayoutHeader from "../components/SettingsLayoutHeader.vue";

const router = useRouter();

const routes = computed(() => [
  {
    label: "Email Notifications",
    route: "/settings/email-notifications",
  },
]);

const notifications = [
  {
    name: "share_feedback",
    label: __("Share Feedback"),
    description: __(
      "Sent to the user who has raised the ticket after the ticket is closed or resolved"
    ),
    route: "/settings/email-notifications/share-feedback",
  },
  {
    name: "acknowledgement",
    label: __("Acknowledgement"),
    description: __("Sent to the user right after creating an email ticket"),
    route: "/settings/email-notifications/acknowledgement",
  },
  {
    name: "reply_to_agents",
    label: __("Reply From Contact"),
    description: __(
      "Sent to all of the assigned agents after a reply from one of the contacts"
    ),
    route: "/settings/email-notifications/reply-from-contact",
  },
  {
    name: "reply_via_agent",
    label: __("Reply From Agent"),
    description: __(
      "Sent to all of the recipients associated with an agent's reply"
    ),
    route: "/settings/email-notifications/reply-from-agent",
  },
];
</script>
