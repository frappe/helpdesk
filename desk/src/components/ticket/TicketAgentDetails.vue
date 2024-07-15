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
import { Badge, Tooltip } from "frappe-ui";
import { dayjs } from "@/dayjs";
import { formatTime } from "@/utils";
import { dateFormat, dateTooltipFormat } from "@/utils";
import { computed } from "vue";

const props = defineProps({
  agreementStatus: {
    type: String,
    required: true,
  },
  ticketCreatedOn: {
    type: String,
    required: true,
  },
  firstRespondedOn: {
    type: String,
    required: true,
  },
  responseBy: {
    type: String,
    required: true,
  },
  resolutionDate: {
    type: String,
    required: true,
  },
  resolutionBy: {
    type: String,
    required: true,
  },
  source: {
    type: String,
    required: true,
  },
});

const firstResponseBadge = computed(() => {
  let firstResponse = null;
  if (!props.firstRespondedOn && dayjs().isBefore(dayjs(props.responseBy))) {
    firstResponse = {
      label: `Due in ${formatTime(dayjs(props.responseBy).diff(dayjs(), "s"))}`,
      color: "orange",
    };
  } else if (dayjs(props.firstRespondedOn).isBefore(dayjs(props.responseBy))) {
    firstResponse = {
      label: `Fulfilled in ${formatTime(
        dayjs(props.firstRespondedOn).diff(dayjs(props.ticketCreatedOn), "s")
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
  if (!props.resolutionDate && dayjs().isBefore(props.resolutionBy)) {
    resolution = {
      label: `Due in ${formatTime(
        dayjs(props.resolutionBy).diff(dayjs(), "s")
      )}`,
      color: "orange",
    };
  } else if (dayjs(props.resolutionDate).isBefore(props.resolutionBy)) {
    resolution = {
      label: `Fulfilled in ${formatTime(
        dayjs(props.resolutionDate).diff(dayjs(props.ticketCreatedOn), "s")
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

const sections = computed(() => [
  {
    label: "First Response",
    tooltipValue: dateFormat(
      props.firstRespondedOn || props.responseBy,
      dateTooltipFormat
    ),
    badgeText: firstResponseBadge.value.label,
    badgeColor: firstResponseBadge.value.color,
  },
  {
    label: "Resolution",
    tooltipValue: dateFormat(
      props.resolutionDate || props.resolutionBy,
      dateTooltipFormat
    ),
    badgeText: resolutionBadge.value.label,
    badgeColor: resolutionBadge.value.color,
  },
  {
    label: "Source",
    value: props.source,
  },
]);
</script>
