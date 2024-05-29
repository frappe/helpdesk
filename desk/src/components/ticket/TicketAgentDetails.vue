<template>
  <div class="flex flex-col gap-3 border-b px-6 py-3">
    <div
      v-for="s in sections"
      :key="s.label"
      class="flex items-center text-base leading-5"
    >
      <div class="w-[126px] text-sm text-gray-600">{{ s.label }}</div>
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

const props = defineProps({
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

let firstResponseBadge;
if (!props.firstRespondedOn && dayjs().isBefore(dayjs(props.responseBy))) {
  firstResponseBadge = {
    label: `Due in ${formatTime(dayjs(props.responseBy).diff(dayjs(), "s"))}`,
    color: "orange",
  };
} else if (dayjs(props.firstRespondedOn).isBefore(dayjs(props.responseBy))) {
  firstResponseBadge = {
    label: `Fulfilled in ${formatTime(
      dayjs(props.firstRespondedOn).diff(dayjs(props.ticketCreatedOn), "s")
    )}`,
    color: "green",
  };
} else {
  firstResponseBadge = {
    label: "Failed",
    color: "red",
  };
}

let resolutionBadge;
if (!props.resolutionDate && dayjs().isBefore(props.resolutionBy)) {
  resolutionBadge = {
    label: `Due in ${formatTime(dayjs(props.resolutionBy).diff(dayjs(), "s"))}`,
    color: "orange",
  };
} else if (dayjs(props.resolutionDate).isBefore(props.resolutionBy)) {
  resolutionBadge = {
    label: `Fulfilled in ${formatTime(
      dayjs(props.resolutionDate).diff(dayjs(props.ticketCreatedOn), "s")
    )}`,
    color: "green",
  };
} else {
  resolutionBadge = {
    label: "Failed",
    color: "red",
  };
}

const sections = [
  {
    label: "First Response",
    tooltipValue: dateFormat(
      props.firstRespondedOn || props.responseBy,
      dateTooltipFormat
    ),
    badgeText: firstResponseBadge.label,
    badgeColor: firstResponseBadge.color,
  },
  {
    label: "Resolution",
    tooltipValue: dateFormat(
      props.resolutionDate || props.resolutionBy,
      dateTooltipFormat
    ),
    badgeText: resolutionBadge.label,
    badgeColor: resolutionBadge.color,
  },
  {
    label: "Source",
    value: props.source,
  },
];
</script>
