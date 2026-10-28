<template>
  <Popover align="end">
    <template #trigger="{ open }">
      <Button variant="subtle" :data-state="open ? 'open' : undefined">
        <template #prefix>
          <span
            class="size-2 rounded-full"
            :class="agentStatusStore.statusColor(agentStatusStore.myStatus)"
            aria-hidden="true"
          />
        </template>
        <!-- the width follows the measured label so the pill eases between lengths -->
        <span
          class="flex overflow-hidden transition-[width] duration-300 ease-out motion-reduce:transition-none"
          :style="labelWidth ? { width: `${labelWidth}px` } : undefined"
        >
          <span
            ref="labelRef"
            class="flex max-w-48 shrink-0 items-center gap-1"
            :title="label"
          >
            <span class="min-w-0 truncate">{{ label }}</span>
            <Transition
              enter-active-class="transition-opacity duration-300 ease-out motion-reduce:transition-none"
              enter-from-class="opacity-0"
            >
              <span
                v-if="remaining"
                class="shrink-0 tabular-nums text-ink-gray-5"
              >
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
      <div class="w-[352px] p-1">
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

const label = computed(() =>
  agentStatusStore.myStatus ? __(agentStatusStore.myStatus) : __("Set status")
);

const { width: labelWidth } = useElementSize(useTemplateRef("labelRef"));

const now = useNow({ interval: 30_000 });

const remaining = computed(() => expiryRemaining(expiresOn.value, now.value));
</script>
