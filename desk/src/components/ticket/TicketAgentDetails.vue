<template>
  <div class="flex flex-col gap-3 border-b px-6 py-3">
    <div
      v-for="s in sections"
      :key="s.label"
      class="flex items-center text-base leading-5"
    >
      <Tooltip :text="s.label">
        <div class="w-[126px] text-sm text-gray-600">{{ s.label }}</div>
      </Tooltip>
      <div class="flex items-center justify-between">
        <div v-if="s.value">{{ s.value }}</div>
        <Tooltip :text="s.tooltipValue">
          <Badge
            v-if="s.badgeText"
            class="-ml-1"
            :class="s.class || null"
            :label="s.badgeText"
            variant="subtle"
            :theme="s.badgeColor"
          />
        </Tooltip>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { dayjs } from "@/dayjs";
import { dateFormat, dateTooltipFormat, formatTime } from "@/utils";
import { Badge, Tooltip } from "frappe-ui";
import { computed, onUnmounted, ref, watch } from "vue";

const props = defineProps({
  ticket: {
    type: Object,
    required: true,
  },
});

let firstResponseInterval = null;
let resolutionInterval = null;

// Reactive variables for countdown times
const firstResponseSeconds = ref(0);
const resolutionSeconds = ref(0);

const firstResponseBadge = computed(() => {
  let firstResponse = null;
  if (
    !props.ticket.first_responded_on &&
    dayjs().isBefore(dayjs(props.ticket.response_by))
  ) {
    let responseBy = formatTime(
      dayjs(props.ticket.response_by).diff(dayjs(), "s")
    );
    if (firstResponseInterval) {
      clearInterval(firstResponseInterval);
      firstResponseInterval = null;
    }
    handleFirstResponseInterval(responseBy);
    firstResponse = {
      label: `Due in ${responseBy}`,
      color: "orange",
    };
  } else if (
    dayjs(props.ticket.first_responded_on).isBefore(
      dayjs(props.ticket.response_by)
    )
  ) {
    firstResponse = {
      label: `Fulfilled in ${formatTime(
        dayjs(props.ticket.first_responded_on).diff(
          dayjs(props.ticket.creation),
          "s"
        )
      )}`,
      color: "green",
    };
  } else {
    firstResponse = {
      label: "Failed",
      color: "red",
    };
  }
  return firstResponse;
});

const resolutionBadge = computed(() => {
  let resolution = null;
  if (resolutionInterval) {
    clearInterval(resolutionInterval);
  }
  if (
    props.ticket.status === "Replied" &&
    props.ticket.on_hold_since &&
    dayjs(props.ticket.resolution_by).isAfter(dayjs(props.ticket.on_hold_since))
  ) {
    let timeLeft = dayjs(props.ticket.resolution_by)
      .add(props.ticket.total_hold_time, "s")
      .diff(dayjs(props.ticket.on_hold_since), "s");
    resolution = {
      label: `${formatTime(timeLeft)} left (On Hold)`,
      color: "blue",
    };
  } else if (
    !props.ticket.resolution_date &&
    dayjs().isBefore(props.ticket.resolution_by)
  ) {
    let resolutionBy = getCalculatedResolution();
    handleResolutionInterval(resolutionBy);

    resolution = {
      label: `Due in ${resolutionBy}`,
      color: "orange",
    };
  } else if (
    dayjs(props.ticket.resolution_date).isBefore(props.ticket.resolution_by)
  ) {
    resolution = {
      label: `Fulfilled in ${formatTime(
        dayjs(props.ticket.resolution_date).diff(
          dayjs(props.ticket.creation),
          "s"
        )
      )}`,
      color: "green",
    };
  } else {
    resolution = {
      label: "Failed",
      color: "red",
    };
  }
  return resolution;
});

function getCalculatedResolution() {
  let resolution = dayjs(props.ticket.resolution_by).add(
    props.ticket.total_hold_time,
    "s"
  );
  // let now = new Date()
  resolution = dayjs(resolution).diff(dayjs(), "s");
  return formatTime(resolution);
}

const sections = computed(() => [
  {
    label: "First Response",
    tooltipValue: dateFormat(
      props.ticket.first_responded_on || props.ticket.response_by,
      dateTooltipFormat
    ),
    badgeText: firstResponseBadge.value.label,
    badgeColor: firstResponseBadge.value.color,
    class: "first-response",
  },
  {
    label: "Resolution",
    tooltipValue: dateFormat(
      props.ticket.resolution_date || props.ticket.resolution_by,
      dateTooltipFormat
    ),
    badgeText: resolutionBadge.value.label,
    badgeColor: resolutionBadge.value.color,
    class: "resolution",
  },
  {
    label: "Source",
    value: props.ticket.via_customer_portal ? "Portal" : "Mail",
  },
]);

// Watch for status changes and clear intervals
watch(
  () => props.ticket.status,
  (newStatus: string) => {
    if (newStatus !== "Open") {
      if (firstResponseInterval) {
        clearInterval(firstResponseInterval);
        firstResponseInterval = null;
      }
      if (resolutionInterval) {
        clearInterval(resolutionInterval);
        resolutionInterval = null;
      }
    }
  },
  { deep: true, immediate: true }
);

function handleFirstResponseInterval(time: string) {
  if (!time) return;
  if (props.ticket.status !== "Open") {
    return;
  }
  let seconds = getTimeInSeconds(time);
  firstResponseInterval = setInterval(() => {
    if (seconds <= 0) {
      clearInterval(firstResponseInterval);
      return;
    }
    seconds--;
    const firstResponseEl = document.querySelector(".first-response");
    if (firstResponseEl) {
      firstResponseEl.textContent = `Due in ${formatTime(seconds)}`;
    }
  }, 1000);
}

function handleResolutionInterval(time: string) {
  if (!time) return;
  if (props.ticket.status !== "Open") {
    return;
  }

  let seconds = getTimeInSeconds(time);
  resolutionInterval = setInterval(() => {
    if (seconds <= 0) {
      clearInterval(resolutionInterval);
      return;
    }
    seconds--;
    const resolutionEl = document.querySelector(".resolution");
    if (resolutionEl) {
      resolutionEl.textContent = `Due in ${formatTime(seconds)}`;
    }
  }, 1000);
}

function getTimeInSeconds(time: string) {
  let timeParts = time.split(" ");
  let seconds = 0;
  timeParts.forEach((part) => {
    if (part.endsWith("d")) {
      seconds += parseInt(part) * 24 * 60 * 60; // days
    } else if (part.endsWith("h")) {
      seconds += parseInt(part) * 60 * 60; // hours
    } else if (part.endsWith("m")) {
      seconds += parseInt(part) * 60; // minutes
    } else if (part.endsWith("s")) {
      seconds += parseInt(part); // seconds
    }
  });
  return seconds;
}

onUnmounted(() => {
  if (firstResponseInterval) {
    clearInterval(firstResponseInterval);
  }
  if (resolutionInterval) {
    clearInterval(resolutionInterval);
  }
  firstResponseInterval = null;
  resolutionInterval = null;
});
</script>
