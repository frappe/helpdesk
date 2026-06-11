<template>
  <div
    class="grid grid-cols-[150px_1fr] items-center gap-x-4 gap-y-3.5 border-b px-5 py-3.5"
  >
    <span class="text-sm text-ink-gray-5">Status</span>
    <span class="break-words text-base font-medium text-ink-gray-9">
      {{ ticket.data.status }}
    </span>

    <span class="text-sm text-ink-gray-5">Priority</span>
    <span class="break-words text-base font-medium text-ink-gray-9">
      {{ ticket.data.priority }}
    </span>

    <template v-for="data in slaData" :key="data.label">
      <Tooltip :text="dayjs(data.value).format('LLLL')">
        <span class="text-sm text-ink-gray-5">{{ data.title }}</span>
      </Tooltip>
      <span class="break-words text-base font-medium text-ink-gray-9">
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
    </template>

    <template v-for="field in customFields" :key="field.fieldname">
      <span class="text-sm text-ink-gray-5">{{ field.label }}</span>
      <span
        class="break-words text-base font-medium text-ink-gray-9"
        :class="!ticket.data[field.fieldname] && 'text-ink-gray-4'"
      >
        {{ ticket.data[field.fieldname] || "—" }}
      </span>
    </template>
  </div>
</template>

<script setup lang="ts">
import { dayjs } from "frappe-ui";
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
