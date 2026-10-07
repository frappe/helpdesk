<template>
  <div v-if="invites.length">
    <h2 class="mt-8 text-base-semibold text-ink-gray-8">
      {{ __("Pending Invites") }}
    </h2>
    <ul class="mt-3 flex flex-col gap-[0.375rem]">
      <li
        v-for="invite in invites"
        :key="invite.invitation"
        class="flex items-center justify-between gap-2 rounded-6 bg-surface-gray-2 px-3 py-1"
      >
        <div class="min-w-0 truncate text-base">
          <span class="text-ink-gray-8">{{ invite.email }}</span>
          <span class="text-ink-gray-5"> ({{ __(invite.role) }})</span>
        </div>
        <Tooltip :text="__('Cancel Invitation')">
          <Button
            icon="lucide-x"
            variant="ghost"
            :aria-label="__('Cancel Invitation')"
            @click="emit('cancel', invite)"
          />
        </Tooltip>
      </li>
    </ul>
  </div>
</template>

<script setup lang="ts">
import { Button, Tooltip } from "frappe-ui";
import { __ } from "@helpdesk/shared/translation";

type Invite = { invitation: string; email: string; role: string };

withDefaults(defineProps<{ invites?: Invite[] }>(), { invites: () => [] });
const emit = defineEmits<{ cancel: [invite: Invite] }>();
</script>
