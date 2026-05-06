<template>
  <SettingsLayoutBase
    :title="__('Email Notifications')"
    :description="
      __(
        'Customize your email notification preferences to stay informed about important updates and activities.'
      )
    "
  >
    <template #content>
      <ul class="isolate -ml-3">
        <div
          v-for="(notification, index) in notifications"
          :key="notification.name"
        >
          <li class="flex items-center justify-between p-3 rounded relative">
            <div class="flex flex-col gap-1">
              <h2
                class="text-base font-medium text-ink-gray-7 relative z-10 pointer-events-none"
              >
                {{ __(notification.label) }}
              </h2>
              <p
                class="text-sm text-ink-gray-5 truncate relative z-10 pointer-events-none"
              >
                {{ __(notification.description) }}
              </p>
            </div>
            <FeatherIcon
              name="chevron-right"
              class="text-ink-gray-7 size-4 relative z-10 pointer-events-none"
            />
            <div
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
            </div>
          </li>
          <hr v-if="index < notifications.length - 1" class="mx-2" />
        </div>
      </ul>
    </template>
  </SettingsLayoutBase>
</template>

<script setup lang="ts">
import { __ } from "@/translation";
import type { AtLeastOneNotifcation, Notification } from "./types";
import SettingsLayoutBase from "@/components/layouts/SettingsLayoutBase.vue";

const props = defineProps<{
  onSelect: (notification: Notification) => void;
}>();

const notifications: AtLeastOneNotifcation = [
  {
    name: "share_feedback",
    label: __("Share feedback"),
    description: __(
      "Sent to the user who has raised the ticket after the ticket is closed or resolved."
    ),
  },
  {
    name: "acknowledgement",
    label: __("Acknowledgement"),
    description: __("Sent to the user right after creating an email ticket."),
  },
  {
    name: "reply_to_agents",
    label: __("Reply from contact"),
    description: __(
      "Sent to all of the agents assigned to the ticket whenever a contact has replied."
    ),
  },
  {
    name: "reply_via_agent",
    label: __("Reply from agent"),
    description: __(
      "Sent to all of the recipients associated with the ticket whenever an agent has replied."
    ),
  },
];
</script>
