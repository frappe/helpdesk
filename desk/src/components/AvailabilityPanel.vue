<template>
  <div>
    <!-- a literal <button>: as="button" resolves to frappe-ui's Button -->
    <button
      v-for="option in agentStatusStore.statusOptions"
      :key="option"
      class="block w-full text-start"
      :aria-pressed="option === agentStatusStore.myStatus"
      @click="pickStatus(option)"
    >
      <ItemListRow class="hover:bg-surface-gray-3">
        <template #prefix>
          <span
            class="size-2 rounded-full"
            :class="agentStatusStore.statusColor(option)"
            aria-hidden="true"
          />
        </template>
        <span class="block truncate" :title="__(option)">{{ __(option) }}</span>
        <template #suffix>
          <span
            v-if="option === agentStatusStore.myStatus"
            class="lucide-check size-4 text-ink-gray-7"
            aria-hidden="true"
          />
        </template>
      </ItemListRow>
    </button>

    <!-- grows from 0fr so the panel eases to its new height -->
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
            <div class="flex items-center justify-between gap-2">
              <TabButtons
                v-model="activePreset"
                :options="presetOptions"
                :aria-label="__('Clear after')"
              />
              <Button
                theme="red"
                variant="ghost"
                icon="lucide-timer-reset"
                :tooltip="__('Clear now')"
                :aria-label="__('Clear now')"
                @click="clearNow"
              />
            </div>
          </div>
        </div>
      </div>
    </Transition>
  </div>
</template>

<script setup lang="ts">
import { useAgentStatusStore } from "@/stores/agentStatus";
import { expiryLabel, expiryPresets } from "@/stores/statusExpiry";
import { __ } from "@/translation";
import { Button, ItemListRow, TabButtons } from "frappe-ui";
import { computed } from "vue";

const emit = defineEmits<{ close: [] }>();

const agentStatusStore = useAgentStatusStore();

const expiresLabel = computed(() =>
  expiryLabel(agentStatusStore.myStatusExpiresOn)
);

const presets = expiryPresets();
const presetOptions = presets.map((preset) => ({
  label: preset.short,
  value: preset.label,
}));

const activePreset = computed({
  get: () => presets.find(agentStatusStore.isExpiryPresetActive)?.label,
  set: (label) => {
    const preset = presets.find((preset) => preset.label === label);
    if (preset) agentStatusStore.applyExpiryPreset(preset);
  },
});

// stays open on an away status, so the timer can be picked next
function pickStatus(option: string) {
  agentStatusStore.setMyStatus(option);
  if (!agentStatusStore.statusCanExpire(option)) emit("close");
}

function clearNow() {
  agentStatusStore.clearMyStatus();
  emit("close");
}
</script>
