<template>
  <Popover
    placement="right-start"
    class="flex w-full"
    trigger="hover"
    :hoverDelay="0.1"
    :leaveDelay="0.1"
  >
    <template #target="{ togglePopover }">
      <button
        class="group w-full flex h-7 items-center justify-between rounded px-2 text-base text-ink-gray-8 hover:bg-surface-gray-2"
        @click.prevent="togglePopover()"
      >
        <div class="flex min-w-0 items-center gap-2">
          <div class="flex items-center size-4">
            <span
              class="size-2.5 mx-auto shrink-0 rounded-full"
              :class="agentStatusStore.statusColor(agentStatusStore.myStatus)"
            />
          </div>
          <span class="truncate">
            {{
              agentStatusStore.myStatus
                ? __(agentStatusStore.myStatus)
                : __("Set status")
            }}
          </span>
        </div>
      </button>
    </template>
    <template #body="{ close }">
      <div
        class="flex flex-col mx-3 p-1.5 rounded-lg border border-outline-gray-1 bg-surface-base shadow-xl min-w-[140px]"
      >
        <button
          v-for="option in agentStatusStore.statusOptions"
          :key="option"
          class="flex items-center gap-2 rounded p-1.5 text-sm text-ink-gray-8 hover:bg-surface-gray-2"
          @click="selectStatus(option, close)"
        >
          <span
            class="size-2.5 shrink-0 rounded-full"
            :class="agentStatusStore.statusColor(option)"
          />
          <span class="whitespace-nowrap">{{ __(option) }}</span>
        </button>
      </div>
    </template>
  </Popover>
</template>

<script setup lang="ts">
import { Popover } from "frappe-ui";
import { useAgentStatusStore } from "@/stores/agentStatus";
import { __ } from "@/translation";

const agentStatusStore = useAgentStatusStore();

function selectStatus(status: string, close: () => void) {
  agentStatusStore.setMyStatus(status);
  close();
}
</script>
