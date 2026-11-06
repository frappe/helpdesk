<template>
  <div
    class="hidden flex-1 items-center justify-center bg-surface-gray-1 p-8 lg:sticky lg:top-0 lg:flex lg:h-screen"
    aria-hidden="true"
  >
    <div
      class="w-full max-w-[420px] space-y-4 rounded-xl border border-outline-gray-2 bg-surface-white p-5 shadow-sm"
    >
      <div class="flex items-center justify-between gap-3">
        <div class="flex min-w-0 items-center gap-2">
          <LucideTicket class="size-4 shrink-0 text-ink-gray-6" />
          <p class="truncate text-base font-medium text-ink-gray-9">
            {{ __("Can't sign in to my account") }}
          </p>
        </div>
        <Badge :label="__('Open')" variant="subtle" theme="gray" />
      </div>
      <div class="flex items-start gap-3">
        <Avatar :label="__('Customer')" size="lg" />
        <div class="rounded-lg bg-surface-gray-2 px-3 py-2 text-p-sm text-ink-gray-7">
          {{ __("Hi, I reset my password but the link keeps expiring. Can you help?") }}
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { __ } from "@/translation";
import { Avatar, Badge } from "frappe-ui";
import LucideTicket from "~icons/lucide/ticket";
</script>
