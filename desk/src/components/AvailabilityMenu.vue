<template>
  <Popover align="end">
    <template #trigger="{ open }">
      <!-- one control: what you are, and for how long -->
      <Button variant="subtle" :data-state="open ? 'open' : undefined">
        <template #prefix>
          <span
            class="size-2 rounded-full"
            :class="agentStatusStore.statusColor(agentStatusStore.myStatus)"
            aria-hidden="true"
          />
        </template>
        <!-- the width follows the measured label, so the pill eases between
        any two lengths: status, timer set, changed or cleared -->
        <span
          class="flex overflow-hidden transition-[width] duration-300 ease-out motion-reduce:transition-none"
          :style="labelWidth ? { width: `${labelWidth}px` } : undefined"
        >
          <span ref="labelRef" class="flex shrink-0 items-center gap-1">
            {{
              agentStatusStore.myStatus
                ? __(agentStatusStore.myStatus)
                : __("Set status")
            }}
            <Transition
              enter-active-class="transition-opacity duration-300 ease-out motion-reduce:transition-none"
              enter-from-class="opacity-0"
            >
              <span v-if="remaining" class="tabular-nums text-ink-gray-5">
                · {{ remaining }}
              </span>
            </Transition>
          </span>
        </span>
        <template #suffix>
          <span
            class="lucide-chevron-down size-4 text-ink-gray-5"
            aria-hidden="true"
          />
        </template>
      </Button>
    </template>
    <template #default="{ close }">
      <div class="w-[336px] p-1">
        <AvailabilityPanel @close="close" />
      </div>
    </template>
  </Popover>
</template>

<script setup lang="ts">
import { useAgentStatusStore } from "@/stores/agentStatus";
import { expiryRemaining } from "@/stores/statusExpiry";
import { __ } from "@/translation";
import { useElementSize, useNow } from "@vueuse/core";
import { Button, Popover } from "frappe-ui";
import AvailabilityPanel from "./AvailabilityPanel.vue";
import { computed, useTemplateRef } from "vue";

const agentStatusStore = useAgentStatusStore();

const expiresOn = computed(() => agentStatusStore.myStatusExpiresOn);

const { width: labelWidth } = useElementSize(useTemplateRef("labelRef"));

// useNow is the tick that re-renders the countdown
const now = useNow({ interval: 30_000 });

const remaining = computed(() => expiryRemaining(expiresOn.value, now.value));
</script>
