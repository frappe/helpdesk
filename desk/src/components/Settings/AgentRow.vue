<template>
  <div
    class="grid grid-cols-12 items-center gap-4 h-14 rounded hover:bg-surface-menu-bar"
  >
    <div class="col-span-4 pl-2 flex items-center gap-3 min-w-0">
      <Tooltip :text="statusTooltip">
        <div class="relative shrink-0">
          <Avatar
            :image="agent.user_image"
            :label="agent.agent_name"
            size="xl"
          />
          <div
            v-if="agent.availability"
            class="absolute bottom-0 -right-0.5 size-2 rounded-full outline outline-white outline-1.5"
            :class="statusColor(agent.availability)"
          />
        </div>
      </Tooltip>
      <div class="min-w-0">
        <div class="flex items-center gap-2">
          <p class="text-base font-medium text-ink-gray-7 truncate">
            {{ agent.agent_name }}
          </p>
          <Badge
            v-if="!agent.is_active"
            :label="__('Inactive')"
            theme="gray"
            variant="subtle"
          />
        </div>
        <div class="text-p-sm text-ink-gray-5 truncate">{{ agent.name }}</div>
      </div>
    </div>

    <div class="col-span-3 flex flex-col gap-0.5 min-w-0">
      <template v-if="stats.open_tickets > 0">
        <div class="flex items-baseline gap-1.5">
          <span class="text-lg font-semibold text-ink-gray-9 tabular-nums">
            {{ stats.open_tickets }}
          </span>
          <span class="text-p-sm text-ink-gray-5">{{ __("open") }}</span>
        </div>
        <span
          v-if="stats.open_tickets_delta"
          class="inline-flex items-center gap-1 text-p-sm font-medium -ml-[3px]"
          :style="{ color: deltaColor(stats.open_tickets_delta) }"
        >
          <component
            :is="stats.open_tickets_delta > 0 ? LucideArrowUp : LucideArrowDown"
            class="size-3.5"
          />
          {{ openDeltaLabel }}
        </span>
      </template>
      <span v-else class="text-p-base text-ink-gray-4">
        {{ __("No open tickets") }}
      </span>
    </div>

    <div class="col-span-2 flex flex-col gap-0.5 min-w-0 -ml-4">
      <template v-if="stats.average_first_response_seconds > 0">
        <div class="flex items-center gap-1 whitespace-nowrap">
          <span
            class="text-base font-medium text-ink-gray-8 tabular-nums -ml-0.5"
          >
            {{ averageFirstResponseLabel }}
          </span>
          <span
            class="inline-flex items-center gap-0.5 text-p-sm font-medium tabular-nums"
            :style="{
              color: deltaColor(stats.average_first_response_seconds_delta),
            }"
          >
            <component :is="responseDeltaIcon" class="size-3.5" />
            {{
              formatDurationDelta(stats.average_first_response_seconds_delta)
            }}
          </span>
        </div>
        <span class="text-p-sm text-ink-gray-5">{{
          __("first response")
        }}</span>
      </template>
      <span v-else class="text-p-base text-ink-gray-4">N/A</span>
    </div>

    <div v-if="isManager" class="col-span-2 min-w-0">
      <Select
        class="max-w-32"
        :model-value="currentRole"
        :options="ROLE_OPTIONS"
        @update:model-value="(v) => $emit('update:role', v as string)"
      />
    </div>

    <div
      :class="isManager ? 'col-span-1' : 'col-span-3'"
      class="flex justify-end pr-2"
    >
      <Dropdown :options="kebabOptions" placement="right">
        <Button icon="more-horizontal" variant="ghost" />
      </Dropdown>
    </div>
  </div>
</template>

<script setup lang="ts">
import { statusColor } from "@/composables/useAvailability";
import { __ } from "@/translation";
import { formatTime, prettyDate } from "@/utils";
import { Avatar, Badge, Button, Dropdown, Select, Tooltip } from "frappe-ui";
import { computed } from "vue";
import LucideArrowUp from "~icons/lucide/arrow-up";
import LucideArrowDown from "~icons/lucide/arrow-down";
import LucideArrowRight from "~icons/lucide/arrow-right";

const ROLE_OPTIONS = [
  { label: "Manager", value: "Manager", icon: "lucide-briefcase" },
  { label: "Agent", value: "Agent", icon: "lucide-user" },
];

interface Agent {
  name: string;
  agent_name: string;
  user_image?: string;
  availability?: string;
  availability_changed_on?: string;
  is_active: boolean | number;
}

interface WorkloadStats {
  open_tickets: number;
  open_tickets_delta: number;
  average_first_response_seconds: number;
  average_first_response_seconds_delta: number;
  teams: string[];
  team_open_tickets: number;
}

const props = defineProps<{
  agent: Agent;
  stats: WorkloadStats;
  isManager: boolean;
  currentRole: string;
  kebabOptions: { label: string; icon: string; onClick: () => void }[];
}>();

defineEmits<{
  "update:role": [role: string];
}>();

const averageFirstResponseLabel = computed(() =>
  formatTime(props.stats.average_first_response_seconds, {
    day: true,
    hour: true,
    minute: true,
    second: false,
  }).trim()
);

// Higher open count / slower response = bad → red; lower = good → green;
// no change → neutral gray.
function deltaColor(delta: number): string {
  if (delta === 0) return "var(--ink-gray-5)";
  return delta > 0 ? "var(--ink-red-4)" : "var(--ink-green-3)";
}

const statusTooltip = computed(() => {
  const { availability, availability_changed_on } = props.agent;
  if (!availability) return __("Unknown");
  if (availability === "Active") return __("Active now");
  const elapsed = availability_changed_on
    ? prettyDate(availability_changed_on, true)?.toLowerCase()
    : "";
  return elapsed ? `${availability} · ${elapsed}` : availability;
});

const responseDeltaIcon = computed(() => {
  const delta = props.stats.average_first_response_seconds_delta;
  if (delta === 0) return LucideArrowRight;
  return delta > 0 ? LucideArrowUp : LucideArrowDown;
});

const openDeltaLabel = computed(() => {
  const delta = props.stats.open_tickets_delta;
  const count = Math.abs(delta);
  if (delta > 0) {
    return count === 1
      ? __("1 more this week")
      : __("{0} more this week", [count]);
  }
  return count === 1
    ? __("1 fewer this week")
    : __("{0} fewer this week", [count]);
});

function formatDurationDelta(seconds: number): string {
  if (seconds === 0) return "0m";
  const abs = Math.abs(seconds);
  const label =
    formatTime(abs, {
      day: true,
      hour: true,
      minute: true,
      second: false,
    }).trim() || "0m";
  return `${seconds > 0 ? "+" : "-"}${label}`;
}
</script>
