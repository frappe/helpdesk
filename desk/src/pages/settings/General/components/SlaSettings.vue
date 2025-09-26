<template>
  <div>
    <div class="text-lg font-semibold text-gray-900">SLAs</div>
    <div class="mt-6 flex flex-col gap-6">
      <div class="flex items-center justify-between">
        <div class="flex flex-col gap-1">
          <span class="text-base font-medium text-ink-gray-8">Track SLA</span>
          <span class="text-p-sm text-ink-gray-6"
            >Monitor and enforce response and resolution times for
            tickets.</span
          >
        </div>
        <Switch />
      </div>
      <div class="flex items-center justify-between">
        <div class="flex flex-col gap-1">
          <span class="text-base font-medium text-ink-gray-8"
            >Allow Resetting SLA</span
          >
          <span class="text-p-sm text-ink-gray-6"
            >Permit SLA timers to be restarted when a ticket is reopened or
            updated.</span
          >
        </div>
        <Switch />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Switch } from "frappe-ui";
</script>
