<template>
  <div class="grid grid-cols-3 md:grid-cols-1 gap-4 border-b px-5 py-2.5">
    <div class="space-y-1.5">
      <span class="block text-sm text-gray-700"> Status </span>
      <span class="block break-words text-base font-medium text-gray-900">
        {{ ticket.data.status }}
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
          {{ dayjs.tz(data.value).fromNow() }}
        </span>
      </span>
    </div>
    <div
      v-for="field in customFields"
      :key="field.fieldname"
      class="space-y-1.5"
    >
      <span class="block text-sm text-gray-700">
        {{ field.label }}
      </span>
      <span
        class="block break-words text-base font-medium text-gray-900"
        :class="!ticket.data[field.fieldname] && 'text-ink-gray-4'"
      >
        {{ ticket.data[field.fieldname] || "—" }}
      </span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { dayjs } from "@/dayjs";
import { Field } from "@/types";
import { computed, inject } from "vue";
import { ITicket } from "./symbols";

const ticket = inject(ITicket);

const slaData = computed(() => {
  const responseSla =
    ticket.data.first_responded_on &&
    dayjs(ticket.data.first_responded_on).isBefore(ticket.data.response_by)
      ? "Fulfilled"
      : "Failed";

  //TODO: no resolution date for unclassified tickets, configurable?
  if (ticket.data.priority === "Unclassified") {
    return [
      {
        title: "Expected First Response",
        showSla: ticket.data.first_responded_on,
        label: responseSla,
        theme: responseSla === "Fulfilled" ? "green" : "red",
        value: ticket.data.response_by,
      },
    ];
  }

  const resolutionSla =
    ticket.data.resolution_date &&
    dayjs(ticket.data.resolution_date).isBefore(ticket.data.resolution_by)
      ? "Fulfilled"
      : "Failed";

  return [
    {
      title: "Expected First Response",
      showSla: ticket.data.first_responded_on,
      label: responseSla,
      theme: responseSla === "Fulfilled" ? "green" : "red",
      value: ticket.data.response_by,
    },
    {
      title: "Expected Resolution",
      showSla: ticket.data.resolution_date,
      label: resolutionSla,
      theme: resolutionSla === "Fulfilled" ? "green" : "red",
      value: ticket.data.resolution_by,
    },
  ];
});

const customFields = computed(() => {
  const _custom_fields = ticket.data.template.fields
    .filter((field: Field) => !field.hide_from_customer)
    .filter(
      (f: Field) => ["subject", "team", "priority"].indexOf(f.fieldname) === -1
    );
  return _custom_fields;
});
</script>
