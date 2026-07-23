<template>
  <div class="space-y-2 px-6 py-3.5 border-b">
    <div class="flex items-center gap-4">
      <span class="w-[150px] shrink-0 text-sm text-ink-gray-5">Status</span>
      <span
        class="flex-1 truncate rounded border border-outline-gray-2 bg-surface-base px-2 py-1 text-base-medium text-ink-gray-9"
      >
        {{ ticket.data.status }}
      </span>
    </div>

    <div class="flex items-center gap-4">
      <span class="w-[150px] shrink-0 text-sm text-ink-gray-5">Priority</span>
      <span
        class="flex-1 truncate rounded border border-outline-gray-2 bg-surface-base px-2 py-1 text-base-medium text-ink-gray-9"
      >
        {{ ticket.data.priority }}
      </span>
    </div>

    <div
      v-for="data in slaData"
      :key="data.label"
      class="flex items-center gap-4"
    >
      <Tooltip :text="dayjs(data.value).format('LLLL')">
        <span class="w-[160px] shrink-0 text-sm text-ink-gray-5">{{
          data.title
        }}</span>
      </Tooltip>
      <Badge
        v-if="data.showSla"
        :label="data.label"
        :theme="data.theme"
        variant="outline"
      />
      <span
        v-else
        class="flex-1 truncate rounded border border-outline-gray-2 bg-surface-base px-2 py-1 text-base-medium text-ink-gray-9"
      >
        {{ dayjs.tz(data.value).fromNow() }}
      </span>
    </div>

    <div
      v-for="field in customFields"
      :key="field.fieldname"
      class="flex items-center gap-4"
    >
      <span class="w-[150px] shrink-0 text-sm text-ink-gray-5">{{
        field.label
      }}</span>
      <span
        class="flex-1 truncate rounded border border-outline-gray-2 bg-surface-base px-2 py-1 text-base-medium"
        :class="
          ticket.data[field.fieldname] ? 'text-ink-gray-9' : 'text-ink-gray-4'
        "
      >
        {{ ticket.data[field.fieldname] || "—" }}
      </span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { dayjs } from "frappe-ui";
import { Field } from "@/types";
import { computed, inject } from "vue";
import { ITicket } from "./symbols";
import { evaluateDependsOnValue } from "@/composables/formCustomisation";

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
    )
    .filter((field: Field) =>
      evaluateDependsOnValue(field.depends_on, ticket.data)
    );
  return _custom_fields;
});
</script>
