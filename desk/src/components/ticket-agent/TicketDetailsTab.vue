<template>
  <div class="h-full">
    <div class="px-5 border-b pb-4">
      <!-- User avatar with buttons -->
      <TicketContact :contact="ticket?.doc.contact" />
      <!-- Core Fields -->
      <div class="">
        <div
          v-for="(section, index) in coreFields"
          :key="index"
          :class="
            section.group ? 'flex gap-2 items-center w-full mb-3' : 'mb-3'
          "
        >
          <Link
            v-for="field in section.fields"
            :key="field.fieldname"
            class="form-control"
            :class="section.group ? 'flex-1' : 'w-full'"
            :page-length="10"
            :label="field.label"
            :placeholder="field.placeholder"
            :doctype="field.doctype"
            :modelValue="field.value"
            @update:model-value="
              (val:string) => handleFieldUpdate(val, field.fieldname)
            "
          />
        </div>

        <!-- Assignee component -->
        <Link
          class="form-control w-full mb-2"
          doctype="HD Team"
          placeholder="Select Team"
          v-model="ticket.doc.raised_by"
          label="Assignee"
          :page-length="10"
        />
        {{ assignees?.data }}
      </div>
    </div>

    <!-- Additional Fields -->
    <div>asds</div>
  </div>
</template>

<script setup lang="ts">
import { Link } from "@/components";
import { useTicket } from "@/composables/useTicket";
import { getMeta } from "@/stores/meta";
import { TicketSymbol } from "@/types";
import { computed, inject } from "vue";
import TicketContact from "./TicketContact.vue";

const ticket = inject(TicketSymbol);
const { assignees } = useTicket(ticket.value.name);
const { getFields, getField } = getMeta("HD Ticket");

const coreFields = computed(() => {
  const fields = getFields();
  if (!fields || fields.length === 0) {
    return [];
  }
  // config driven core fields
  const _coreFields = [
    { group: true, fields: [getField("ticket_type"), getField("priority")] },
    { group: false, fields: [getField("customer")] },
    { group: true, fields: [getField("agent_group")] },
  ];
  debugger;
  _coreFields.forEach((section) => {
    section.fields = section.fields.map((f) => {
      return {
        label: f.label,
        value: ticket.value.doc[f.fieldname],
        doctype: f.options,
        placeholder: `Select ${f.label}`,
        fieldname: f.fieldname,
      };
    });
  });
  return _coreFields;
});

function handleFieldUpdate(value: string, fieldname: string) {
  if (ticket.value.doc[fieldname] === value) return;
  ticket.value.setValue.submit({ [fieldname]: value });
}
</script>

<style scoped>
:deep(.form-control button) {
  @apply text-base rounded h-7 py-1.5 border border-outline-gray-2 bg-surface-white placeholder-ink-gray-4 hover:border-outline-gray-3 hover:shadow-sm focus:bg-surface-white focus:border-outline-gray-4 focus:shadow-sm focus:ring-0 focus-visible:ring-0 text-ink-gray-8 transition-colors w-full dark:[color-scheme:dark];
}
:deep(.form-control button > div) {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

:deep(.form-control div) {
  width: 100%;
  display: flex;
}
</style>
