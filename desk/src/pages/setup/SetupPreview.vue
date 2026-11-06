<template>
  <div
    class="hidden flex-1 items-center justify-center bg-surface-gray-1 p-8 lg:sticky lg:top-0 lg:flex lg:h-screen"
    aria-hidden="true"
  >
    <div class="w-full max-w-sm space-y-4">
      <div class="flex items-center gap-2 text-sm">
        <LucideMail class="size-4 shrink-0 text-ink-gray-5" />
        <span
          class="truncate"
          :class="mailbox ? 'text-ink-gray-8' : 'text-ink-gray-5'"
        >
          {{ mailbox || __("Your support mailbox") }}
        </span>
      </div>

      <div
        class="rounded-lg border bg-surface-elevation-1"
        :class="
          arrived
            ? 'border-outline-gray-1 shadow-md'
            : 'border-dashed border-outline-gray-3'
        "
      >
        <div class="flex items-center gap-2 px-4 py-3">
          <template v-if="arrived">
            <span class="text-sm tabular-nums text-ink-gray-4">#1042</span>
            <span class="truncate text-base-semibold text-ink-gray-8">
              {{ __("Can't reset my password") }}
            </span>
            <Badge
              :label="__('Open')"
              theme="gray"
              variant="subtle"
              class="ml-auto"
            />
          </template>
          <span v-else class="text-p-sm text-ink-gray-5">
            {{
              mailbox
                ? __("Your first ticket will show up here")
                : __("Connect a mailbox to bring tickets in")
            }}
          </span>
        </div>

        <div v-if="arrived" class="flex items-start gap-2.5 px-4 pb-4">
          <Avatar
            :label="__('Maya Fernandez')"
            :image="avatarFor('maya-fernandez')"
            size="md"
          />
          <div class="min-w-0 flex-1">
            <span class="text-sm-semibold text-ink-gray-8">{{
              __("Maya Fernandez")
            }}</span>
            <p class="text-p-sm text-ink-gray-7">
              {{
                __(
                  "The reset link in the email says it has expired. Could you send me a new one?"
                )
              }}
            </p>
          </div>
        </div>
      </div>

      <div v-if="invitees.length" class="flex items-center gap-3">
        <div class="flex -space-x-2">
          <Avatar
            v-for="invitee in shown"
            :key="invitee.email"
            :label="invitee.email"
            :image="avatarFor(invitee.email)"
            size="md"
            class="ring-2 ring-surface-gray-1"
          />
        </div>
        <span class="text-p-sm text-ink-gray-6">
          {{
            invitees.length === 1
              ? __("1 agent joining")
              : __("{0} agents joining", [invitees.length])
          }}
        </span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { __ } from "@/translation";
import { createAvatar } from "@dicebear/core";
import * as lorelei from "@dicebear/lorelei";
import { Avatar, Badge } from "frappe-ui";
import { computed } from "vue";
import LucideMail from "~icons/lucide/mail";

const props = defineProps<{
  mailbox: string | null;
  arrived: boolean;
  invitees: { email: string }[];
}>();

const shown = computed(() => props.invitees.slice(0, 5));

const avatarFor = (seed: string) =>
  createAvatar(lorelei, { seed }).toDataUri();
</script>
