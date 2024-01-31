<template>
  <span class="grid grid-cols-1 gap-4 border-b px-5 py-2.5 sm:grid-cols-3">
    <div class="space-y-1.5">
      <span class="block text-sm text-gray-700"> Status </span>
      <span class="block break-words text-base font-medium text-gray-900">
        {{ transformStatus(ticket.data.status) }}
      </span>
    </div>
    <div class="space-y-1.5">
      <span class="block text-sm text-gray-700"> Priority </span>
      <span class="block break-words text-base font-medium text-gray-900">
        {{ ticket.data.priority }}
      </span>
    </div>
    <div v-for="data in slaData" :key="data.label" class="space-y-1.5">
      <Tooltip :text="dayjs(data.value).long()">
          <span class="block text-sm text-gray-700">{{ data.title }}</span>
      </Tooltip>
      <span class="block break-words text-base font-medium text-gray-900">
        <Badge
          v-if="data.showSla"
          :label="data.label"
          :theme="data.theme"
          variant="outline"
        />
        <span v-else>
          {{ dayjs(data.value).fromNow() }}
        </span>
      </span>
    </div>
    <div
      v-for="field in ticket.data.template.fields.filter(
        (f) => !f.hide_from_customer
      )"
      :key="field.fieldname"
      class="space-y-1.5"
    >
      <span class="block text-sm text-gray-700">
        {{ field.label }}
      </span>
      <span class="block break-words text-base font-medium text-gray-900">
        {{ ticket.data[field.fieldname] }}
      </span>
    </div>
  </span>
</template>

<script setup lang="ts">
import { inject, computed } from "vue";
import { ITicket } from "./symbols";
import { dayjs } from "@/dayjs";

const ticket = inject(ITicket);

const slaData = computed(() => {
  const responseSla =
    ticket.data.first_responded_on &&
    dayjs(ticket.data.first_responded_on).isBefore(ticket.data.response_by)
      ? "Fulfilled"
      : "Failed";
  const resolutionSla =
    ticket.data.resolution_date &&
    dayjs(ticket.data.resolution_date).isBefore(ticket.data.resolution_by)
      ? "Fulfilled"
      : "Failed";

  return [
    {
      title: "First Response",
      showSla: ticket.data.first_responded_on,
      label: responseSla,
      theme: responseSla === "Fulfilled" ? "green" : "red",
      value: ticket.data.response_by,
    },
    {
      title: "Resolution",
      showSla: ticket.data.resolution_date,
      label: resolutionSla,
      theme: resolutionSla === "Fulfilled" ? "green" : "red",
      value: ticket.data.resolution_by,
    },
  ];
});

function transformStatus(status: string) {
  switch (status) {
    case "Replied":
      return "Awaiting reply";
    default:
      return status;
  }
}
</script>
