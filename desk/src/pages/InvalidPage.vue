<template>
  <div
    class="grid h-full place-items-center px-4 py-20 text-center text-md text-ink-gray-5"
  >
    <div class="space-y-4">
      <div class="flex justify-center items-center mx-auto">
        <LucideFileX class="size-10 text-ink-gray-4" />
      </div>
      <div class="flex flex-col gap-1">
        <div class="text-md-medium text-ink-gray-8">
          {{ __("Page not found") }}
        </div>
        <div class="text-center text-p-base text-ink-gray-6 mt-1">
          {{
            __(
              "You don't have permission to view this page, or it no longer exists."
            )
          }}
        </div>
      </div>
      <Button :route="{ name: 'TicketsAgent' }" variant="subtle">
        <template #prefix>
          <span class="lucide-arrow-left size-4" aria-hidden="true" />
        </template>
        {{ __("Back to Tickets") }}
      </Button>
    </div>
  </div>
</template>

<script setup>
import { Button } from "frappe-ui";
import { __ } from "@/translation";
</script>
