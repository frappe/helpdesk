<template>
  <div class="flex flex-col gap-2 border-b px-6 py-3">
    <div
      v-for="s in sections"
      :key="s.label"
      class="flex items-center gap-2 text-base leading-5"
    >
      <div class="w-[106px] text-sm text-gray-600">{{ s.label }}</div>
      <div class="flex items-center justify-between gap-2.5">
        <div>{{ s.value }}</div>
        <Badge
          v-if="s.badgeText"
          class="-ml-1"
          :label="s.badgeText"
          variant="subtle"
          :theme="s.badgeColor"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Badge } from "frappe-ui";
import { dayjs } from "@/dayjs";

const props = defineProps({
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
if (!props.firstRespondedOn) {
  firstResponseBadge = {
    label: "Due",
    color: "orange",
  };
} else if (dayjs(props.firstRespondedOn).isBefore(dayjs(props.responseBy))) {
  firstResponseBadge = {
    label: "Fulfilled",
    color: "green",
  };
} else {
  firstResponseBadge = {
    label: "Failed",
    color: "red",
  };
}

let resolutionBadge;
if (!props.resolutionDate) {
  resolutionBadge = {
    label: "Due",
    color: "orange",
  };
} else if (dayjs(props.resolutionDate).isBefore(props.resolutionBy)) {
  resolutionBadge = {
    label: "Fulfilled",
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
    value: dayjs(props.firstRespondedOn || props.responseBy).short(),
    badgeText: firstResponseBadge.label,
    badgeColor: firstResponseBadge.color,
  },
  {
    label: "Resolution",
    value: dayjs(props.resolutionDate || props.resolutionBy).short(),
    badgeText: resolutionBadge.label,
    badgeColor: resolutionBadge.color,
  },
  {
    label: "Source",
    value: props.source,
  },
];
</script>
