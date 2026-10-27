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
        <!-- a literal <button>: as="button" resolves to frappe-ui's Button -->
        <button
          v-for="option in agentStatusStore.statusOptions"
          :key="option"
          class="block w-full text-start"
          :aria-pressed="option === agentStatusStore.myStatus"
          @click="pickStatus(option, close)"
        >
          <ItemListRow class="hover:bg-surface-gray-3">
            <template #prefix>
              <span
                class="size-2 rounded-full"
                :class="agentStatusStore.statusColor(option)"
                aria-hidden="true"
              />
            </template>
            {{ __(option) }}
            <template #suffix>
              <span
                v-if="option === agentStatusStore.myStatus"
                class="lucide-check size-4 text-ink-gray-7"
                aria-hidden="true"
              />
            </template>
          </ItemListRow>
        </button>

        <!-- the timer only means something away from Active. The row grows
        from 0fr so the popover eases to its new height instead of jumping -->
        <Transition
          enter-active-class="transition-[grid-template-rows,opacity] duration-300 ease-out motion-reduce:transition-none [&>*]:overflow-hidden"
          enter-from-class="!grid-rows-[0fr] opacity-0"
          leave-active-class="transition-[grid-template-rows,opacity] duration-200 ease-in motion-reduce:transition-none [&>*]:overflow-hidden"
          leave-to-class="!grid-rows-[0fr] opacity-0"
        >
          <div
            v-if="agentStatusStore.statusCanExpire(agentStatusStore.myStatus)"
            class="grid grid-rows-[1fr]"
          >
            <div class="min-h-0">
              <div
                class="mt-1 space-y-2 border-t border-outline-gray-1 px-2 pb-1 pt-2.5"
              >
                <div class="flex items-baseline justify-between">
                  <p class="text-sm text-ink-gray-5">{{ __("Clear after") }}</p>
                  <p class="text-sm tabular-nums text-ink-gray-5">
                    <Transition
                      mode="out-in"
                      enter-active-class="transition duration-150 ease-out motion-reduce:transition-none"
                      enter-from-class="translate-y-1 opacity-0"
                      leave-active-class="transition duration-100 ease-in motion-reduce:transition-none"
                      leave-to-class="-translate-y-1 opacity-0"
                    >
                      <span :key="expiresLabel" class="inline-block">
                        {{ expiresLabel }}
                      </span>
                    </Transition>
                  </p>
                </div>
                <div class="flex flex-wrap justify-between gap-1">
                  <Button
                    v-for="preset in expiryPresets()"
                    :key="preset.label"
                    size="xs"
                    :label="preset.short"
                    :data-state="
                      agentStatusStore.isExpiryPresetActive(preset)
                        ? 'active'
                        : undefined
                    "
                    :aria-pressed="
                      agentStatusStore.isExpiryPresetActive(preset)
                    "
                    @click="agentStatusStore.applyExpiryPreset(preset)"
                  />
                  <Button
                    size="xs"
                    icon="lucide-timer-reset"
                    :tooltip="__('Clear now')"
                    :aria-label="__('Clear now')"
                    @click="clearNow(close)"
                  />
                </div>
              </div>
            </div>
          </div>
        </Transition>
      </div>
    </template>
  </Popover>
</template>

<script setup lang="ts">
import { useAgentStatusStore } from "@/stores/agentStatus";
import {
  expiryLabel,
  expiryPresets,
  expiryRemaining,
} from "@/stores/statusExpiry";
import { __ } from "@/translation";
import { useElementSize, useNow } from "@vueuse/core";
import { Button, ItemListRow, Popover } from "frappe-ui";
import { computed, useTemplateRef } from "vue";

const agentStatusStore = useAgentStatusStore();

const expiresOn = computed(() => agentStatusStore.myStatusExpiresOn);
const expiresLabel = computed(() => expiryLabel(expiresOn.value));

const { width: labelWidth } = useElementSize(useTemplateRef("labelRef"));

// useNow is the tick that re-renders the countdown
const now = useNow({ interval: 30_000 });

const remaining = computed(() => expiryRemaining(expiresOn.value, now.value));

// stays open on an away status, so the timer can be picked next
function pickStatus(option: string, close: () => void) {
  agentStatusStore.setMyStatus(option);
  if (!agentStatusStore.statusCanExpire(option)) close();
}

function clearNow(close: () => void) {
  agentStatusStore.clearMyStatus();
  close();
}
</script>
