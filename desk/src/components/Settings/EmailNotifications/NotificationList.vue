<template>
  <!-- Header -->
  <div class="pt-8 pb-2 bg-white sticky top-0 z-10">
    <SettingsLayoutHeader
      :title="__('Email Notifications')"
      :description="
        __(
          'Customize your email notification preferences to stay informed about important updates and activities.'
        )
      "
    />
  </div>
  <!-- Body -->
  <ul class="mt-4 pb-8 isolate">
    <li
      v-for="notification in notifications"
      :key="notification.name"
      class="flex items-center justify-between p-3 rounded relative"
    >
      <div class="flex flex-col gap-1">
        <h2
          class="text-base font-medium text-ink-gray-7 relative z-10 pointer-events-none"
        >
          {{ notification.label }}
        </h2>
        <p
          class="text-sm text-ink-gray-5 truncate relative z-10 pointer-events-none"
        >
          {{ notification.description }}
        </p>
      </div>
      <FeatherIcon
        name="chevron-right"
        class="text-ink-gray-7 size-4 relative z-10 pointer-events-none"
      />
      <button
        type="button"
        class="w-full h-full absolute top-0 left-0 hover:bg-gray-50 rounded-[inherit]"
        @click="
          () => {
            props.onSelect(notification);
          }
        "
      >
        <span class="sr-only">{{
          __("customize {0}", notification.name)
        }}</span>
      </button>
    </li>
  </ul>
</template>

<script setup lang="ts">
import { __ } from "@/translation";
import SettingsLayoutHeader from "../SettingsLayoutHeader.vue";
import type { AtLeastOneNotifcation, Notification } from "./types";

const props = defineProps<{
  onSelect: (notification: Notification) => void;
}>();

const notifications: AtLeastOneNotifcation = [
  {
    name: "share_feedback",
    label: __("Share Feedback"),
    description: __(
      "Sent to the user who has raised the ticket after the ticket is closed or resolved"
    ),
  },
  {
    name: "acknowledgement",
    label: __("Acknowledgement"),
    description: __("Sent to the user right after creating an email ticket"),
  },
  {
    name: "reply_to_agents",
    label: __("Reply From Contact"),
    description: __(
      "Sent to all of the assigned agents after a reply from one of the contacts"
    ),
  },
  {
    name: "reply_via_agent",
    label: __("Reply From Agent"),
    description: __(
      "Sent to all of the recipients associated with an agent's reply"
    ),
  },
];
</script>
