<template>
  <div v-if="sla" class="p-4 border rounded-lg bg-surface-base shadow-sm space-y-3">
    <!-- Header: Stage & Status Badge -->
    <div class="flex items-center justify-between">
      <div class="flex items-center gap-2">
        <span class="relative flex h-2.5 w-2.5">
          <span
            v-if="!sla.isCompleted"
            :class="[
              'absolute inline-flex h-full w-full rounded-full opacity-75 animate-ping',
              sla.statusColor === 'green' ? 'bg-emerald-400' :
              sla.statusColor === 'yellow' ? 'bg-amber-400' : 'bg-red-400'
            ]"
          ></span>
          <span
            :class="[
              'relative inline-flex rounded-full h-2.5 w-2.5',
              sla.statusColor === 'green' ? 'bg-emerald-500' :
              sla.statusColor === 'yellow' ? 'bg-amber-500' : 'bg-red-500'
            ]"
          ></span>
        </span>
        <span class="text-sm font-semibold text-ink-gray-7">
          {{ __(sla.stage) }} {{ __('SLA') }}
        </span>
      </div>
      <Badge
        :label="sla.isCompleted ? __(sla.finalStatus) : (sla.isOverdue ? __('Overdue') : (sla.isNearDeadline ? __('Near Deadline') : __('On Track')))"
        :theme="sla.statusColor"
        variant="subtle"
      />
    </div>

    <!-- Details -->
    <div v-if="!sla.isCompleted" class="space-y-2">
      <!-- Due Time -->
      <div class="text-xs text-ink-gray-5 flex items-center gap-1.5">
        <LucideCalendar class="size-3.5 text-ink-gray-4" />
        <span><strong class="text-ink-gray-6">{{ __('Due Time:') }}</strong> {{ sla.dueTime }}</span>
      </div>

      <!-- Remaining Time (if on track or near deadline) -->
      <div v-if="!sla.isOverdue" class="space-y-1.5 pt-1">
        <div class="flex justify-between text-xs font-medium text-ink-gray-6">
          <span class="flex items-center gap-1">
            <LucideClock class="size-3.5 text-ink-gray-4" />
            {{ __('Remaining Time:') }} {{ sla.remainingTimeStr }}
          </span>
          <span>{{ sla.remainingPercent.toFixed(0) }}%</span>
        </div>
        <div class="w-full bg-outline-gray-2 rounded-full h-2 overflow-hidden">
          <div
            :class="[
              'h-full rounded-full transition-all duration-500',
              sla.statusColor === 'green' ? 'bg-emerald-500' : 'bg-amber-500'
            ]"
            :style="{ width: `${sla.remainingPercent}%` }"
          ></div>
        </div>
      </div>

      <!-- Alerts -->
      <div
        v-if="sla.isOverdue"
        class="flex items-center gap-2 p-3 bg-red-50 border border-red-200 text-red-800 rounded-lg text-xs font-semibold mt-2"
      >
        <LucideAlertCircle class="size-4 shrink-0 text-red-600 animate-bounce" />
        <span>{{ __("Overdue by {0} hours", [sla.overdueHours]) }}</span>
      </div>

      <div
        v-else-if="sla.isNearDeadline"
        class="flex items-center gap-2 p-3 bg-amber-50 border border-amber-200 text-amber-800 rounded-lg text-xs font-semibold mt-2"
      >
        <LucideAlertTriangle class="size-4 shrink-0 text-amber-600 animate-pulse" />
        <span>{{ __("Escalation Warning") }}</span>
      </div>
    </div>

    <!-- Completed view -->
    <div v-else class="text-xs text-ink-gray-5">
      <span>{{ __('SLA was completed on:') }} {{ sla.completedOn }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from "vue";
import { Badge, dayjs } from "frappe-ui";
import { __ } from "@/translation";

const props = defineProps({
  ticket: {
    type: Object,
    required: true,
  },
});

const tick = ref(0);
let intervalId: any = null;

onMounted(() => {
  intervalId = setInterval(() => {
    tick.value++;
  }, 10000); // Live update every 10 seconds
});

onUnmounted(() => {
  if (intervalId) clearInterval(intervalId);
});

const sla = computed(() => {
  const doc = props.ticket;
  const _t = tick.value; // react to tick updates
  if (!doc) return null;

  let deadlineStr = null;
  let stage = "";
  let isCompleted = false;
  let finalStatus = "";
  let completedOn = "";

  if (!doc.first_responded_on && doc.response_by) {
    deadlineStr = doc.response_by;
    stage = "First Response";
  } else if (!doc.resolution_date && doc.resolution_by) {
    deadlineStr = doc.resolution_by;
    stage = "Resolution";
  } else {
    isCompleted = true;
    if (doc.resolution_date && doc.resolution_by) {
      stage = "Resolution";
      const isFailed = dayjs(doc.resolution_date).isAfter(dayjs(doc.resolution_by));
      finalStatus = isFailed ? "Failed" : "Fulfilled";
      completedOn = dayjs(doc.resolution_date).format("LLL");
    } else if (doc.first_responded_on && doc.response_by) {
      stage = "First Response";
      const isFailed = dayjs(doc.first_responded_on).isAfter(dayjs(doc.response_by));
      finalStatus = isFailed ? "Failed" : "Fulfilled";
      completedOn = dayjs(doc.first_responded_on).format("LLL");
    } else {
      return null; // No SLA configured/active
    }
  }

  const now = dayjs();
  const startTime = dayjs(doc.creation);

  if (isCompleted) {
    return {
      isCompleted: true,
      stage,
      finalStatus,
      completedOn,
      statusColor: finalStatus === "Fulfilled" ? "green" : "red",
    };
  }

  const deadline = dayjs(deadlineStr);
  const totalMs = deadline.diff(startTime);
  const remainingMs = deadline.diff(now);

  const isOverdue = remainingMs < 0;
  const remainingPercent = totalMs > 0 ? (remainingMs / totalMs) * 100 : 0;

  let statusColor = "green";
  if (isOverdue) {
    statusColor = "red";
  } else if (remainingPercent <= 30) {
    statusColor = "yellow";
  }

  // Display: "Overdue by X hours"
  const overdueHours = isOverdue ? (Math.abs(remainingMs) / (1000 * 60 * 60)).toFixed(1) : "0";
  const isNearDeadline = !isOverdue && remainingPercent <= 30;

  return {
    isCompleted: false,
    stage,
    dueTime: deadline.format("LLL"),
    remainingPercent: Math.max(0, Math.min(100, remainingPercent)),
    remainingTimeStr: formatDuration(remainingMs),
    isOverdue,
    overdueHours,
    isNearDeadline,
    statusColor,
  };
});

function formatDuration(ms: number) {
  if (ms < 0) return "Overdue";
  const duration = dayjs.duration(ms);
  const days = duration.days();
  const hours = duration.hours();
  const minutes = duration.minutes();

  if (days > 0) {
    return `${days}d ${hours}h`;
  }
  if (hours > 0) {
    return `${hours}h ${minutes}m`;
  }
  return `${minutes}m`;
}
</script>
