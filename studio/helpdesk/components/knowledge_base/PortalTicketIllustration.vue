<template>
  <!-- Decorative: a resolved ticket on top of two tilted ones. -->
  <div class="relative h-[164px] w-[320px] max-w-full" aria-hidden="true">
    <div
      class="absolute inset-x-5 top-0 h-24 -rotate-3 rounded-[12px] border border-outline-gray-1 bg-surface-gray-1"
    />
    <div
      class="absolute inset-x-7 top-0 h-24 rotate-2 rounded-[12px] border border-outline-gray-1 bg-surface-gray-1"
    />
    <div
      class="absolute inset-x-0 top-6 flex flex-col gap-3 rounded-[12px] border border-outline-gray-2 bg-surface-base p-4 shadow-lg"
    >
      <div class="flex items-center justify-between">
        <span class="text-base text-ink-gray-6">#1024</span>
        <!-- As the ticket list shows a status. -->
        <PortalStatusPill :label="__('Resolved')" color="Green" size="sm" />
      </div>
      <div class="flex flex-col gap-2">
        <span class="h-2 w-3/4 rounded-full bg-surface-gray-2" />
        <span class="h-2 w-1/2 rounded-full bg-surface-gray-2" />
      </div>
      <div class="flex items-center gap-2">
        <Avatar class="shrink-0" size="md" label="Maya Reed" />
        <span class="text-sm text-ink-gray-6">
          {{ __("Replied in {0}", ["1h 12m"]) }}
        </span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Avatar } from "frappe-ui";
import { __ } from "@helpdesk/shared/translation";
import PortalStatusPill from "../ticket/PortalStatusPill.vue";
</script>
