<template>
  <div class="space-y-2 px-6 py-3.5 border-b">
    <div class="flex items-center gap-4">
      <span class="w-[150px] shrink-0 text-p-sm text-ink-gray-5">Status</span>
      <span
        class="flex-1 truncate rounded border border-outline-gray-2 bg-surface-base px-2 py-1 text-p-sm text-ink-gray-9"
      >
        {{ ticket.data.status }}
      </span>
    </div>

    <div class="flex items-center gap-4">
      <span class="w-[150px] shrink-0 text-p-sm text-ink-gray-5">Priority</span>
      <span
        class="flex-1 truncate rounded border border-outline-gray-2 bg-surface-base px-2 py-1 text-p-sm text-ink-gray-9"
      >
        {{ ticket.data.priority }}
      </span>
    </div>

    <div
      v-for="data in slaData"
      :key="data.title"
      class="flex items-center gap-4"
    >
      <Tooltip :text="dayjs(data.value).format('LLLL')">
        <span class="w-[150px] shrink-0 text-p-sm text-ink-gray-5">{{
          data.title
        }}</span>
      </Tooltip>
      <span class="flex-1 truncate text-p-sm" :class="data.textColor">
        {{ __(data.label) }}
      </span>
    </div>

    <div
      v-for="field in customFields"
      :key="field.fieldname"
      class="flex items-center gap-4"
    >
      <span class="w-[150px] shrink-0 text-p-sm text-ink-gray-5">{{
        field.label
      }}</span>
      <span
        class="flex-1 truncate rounded border border-outline-gray-2 bg-surface-base px-2 py-1 text-p-sm"
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
import {
  slaLabel,
  slaTextColor,
  useSLA,
  type SLAMetric,
} from "@/composables/useSLA";
import { Field } from "@/types";
import { computed, inject } from "vue";
import { ITicket } from "./symbols";

const ticket = inject(ITicket);

const { firstResponse, resolution } = useSLA(
  computed(() => ({ doc: ticket.data }))
);

const slaData = computed(() =>
  [
    { title: "Expected First Response", metric: firstResponse.value },
    { title: "Expected Resolution", metric: resolution.value },
  ]
    .filter((row): row is { title: string; metric: SLAMetric } =>
      Boolean(row.metric)
    )
    .map((row) => ({
      title: row.title,
      value: row.metric.dueBy,
      label: slaLabel(row.metric),
      textColor: slaTextColor(row.metric),
    }))
);

const customFields = computed(() => {
  const _custom_fields = ticket.data.template.fields
    .filter((field: Field) => !field.hide_from_customer)
    .filter(
      (f: Field) => ["subject", "team", "priority"].indexOf(f.fieldname) === -1
    );
  return _custom_fields;
});
</script>
