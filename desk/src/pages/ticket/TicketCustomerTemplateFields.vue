<template>
  <span class="grid grid-cols-1 border-b px-5 py-2.5 sm:grid-cols-3">
    <div class="space-y-1.5">
      <span class="block text-sm text-gray-700"> Status </span>
      <span class="block break-words text-base font-medium text-gray-900">
        {{ transformStatus(ticket.data.status) }}
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
import { inject } from "vue";
import { ITicket } from "./symbols";

const ticket = inject(ITicket);

function transformStatus(status: string) {
  switch (status) {
    case "Replied":
      return "Awaiting reply";
    default:
      return status;
  }
}
</script>
