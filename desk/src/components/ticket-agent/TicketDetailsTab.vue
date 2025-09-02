<template>
  <div
    class="h-full overflow-y-hidden flex flex-1 flex-col justify-between overflow-hidden"
  >
    <div class="px-5 pb-4 flex flex-col">
      <!-- User avatar with buttons -->
      <TicketContact />
      <!-- Core Fields -->
      <div>
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
            class="form-control-core"
            :class="section.group ? 'flex-1' : 'w-full'"
            :page-length="10"
            :label="field.label"
            :placeholder="field.placeholder"
            :doctype="field.doctype"
            :modelValue="field.value"
            :required="field.required"
            @update:model-value="
              (val:string) => handleFieldUpdate(field.fieldname, val)
            "
          />
        </div>

        <!-- Assignee component -->
        <AssigneeTo />
      </div>
    </div>

    <!-- Additional Fields -->
    <div
      class="border-t flex flex-col pb-5 flex-1 h-full overflow-hidden pb-12"
    >
      <div class="overflow-y-scroll">
        <TicketField
          v-for="field in customFields"
          :key="field.fieldname"
          :field="field"
          :value="field.value"
          @change="
            ({ fieldname, value }) => handleFieldUpdate(fieldname, value)
          "
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Link } from "@/components";
import { getMeta } from "@/stores/meta";
import {
  AssigneeSymbol,
  CustomizationSymbol,
  FieldValue,
  TicketSymbol,
} from "@/types";
import { toast } from "frappe-ui";
import { computed, inject } from "vue";
import TicketField from "../TicketField.vue";
import AssigneeTo from "./AssignTo.vue";
import TicketContact from "./TicketContact.vue";

const ticket = inject(TicketSymbol);
const assignees = inject(AssigneeSymbol);
const customizations = inject(CustomizationSymbol);
const { getFields, getField } = getMeta("HD Ticket");

// ticket_type, priority, customer, agent_group
const coreFields = computed(() => {
  const fieldsMeta = getFields();
  if (!fieldsMeta || fieldsMeta.length === 0) {
    return [];
  }
  const _coreFields = [
    { group: true, fields: [getField("ticket_type"), getField("priority")] },
    { group: false, fields: [getField("customer")] },
    { group: true, fields: [getField("agent_group")] },
  ];

  _coreFields.forEach((section) => {
    section.fields = section.fields.map((f) => {
      return {
        label: f.label,
        value: ticket.value.doc[f.fieldname],
        doctype: f.options,
        placeholder: `Select ${f.label}`,
        fieldname: f.fieldname,
        required: f.reqd,
      };
    });
  });
  return _coreFields;
});

const customFields = computed(() => {
  const fieldsMeta = getFields();
  if (!fieldsMeta || fieldsMeta.length === 0) {
    return [];
  }

  if (!customizations.value.data || customizations.value.loading) return [];
  let customFields = customizations.value.data?.custom_fields || [];
  const _coreFields = [
    "ticket_type",
    "priority",
    "customer",
    "agent_group",
    "subject",
    "status",
  ];
  customFields = customFields.filter((f) => !_coreFields.includes(f.fieldname));
  let _customFields = customFields.map((f) => {
    const fieldMeta = getField(f.fieldname);
    return {
      label: fieldMeta?.label || f.fieldname,
      value: ticket.value.doc[f.fieldname],
      fieldname: f.fieldname,
      fieldtype: fieldMeta?.fieldtype,
      doctype: fieldMeta?.options || "",
      options: fieldMeta?.options || "",
      placeholder: f.placeholder || `Enter ${fieldMeta?.label || f.fieldname}`,
      required: f.required || fieldMeta.reqd,
      url_method: f.url_method || "",
      readonly: Boolean(fieldMeta.read_only),
      disabled: Boolean(fieldMeta.read_only),
    };
  });
  return _customFields;

  // customFields
});

function handleFieldUpdate(fieldname: string, value: FieldValue) {
  if (ticket.value.doc[fieldname] === value) return;
  ticket.value.setValue.submit(
    { [fieldname]: value },
    {
      onSuccess: () => {
        // TODO: emit the event for notification to listeners
        if (fieldname === "agent_group") {
          assignees.value.reload();
        }
      },
      onError: (error) => {
        const msg = error.exc_type
          ? (error.messages || error.message || []).join(", ")
          : error.message;
        toast.error(msg);
      },
    }

    //show error toast
  );
}
</script>

<style scoped>
:deep(.form-control-core button) {
  @apply text-base rounded h-7 py-1.5 border border-outline-gray-2 bg-surface-white placeholder-ink-gray-4 hover:border-outline-gray-3 hover:shadow-sm focus:bg-surface-white focus:border-outline-gray-4 focus:shadow-sm focus:ring-0 focus-visible:ring-0 text-ink-gray-8 transition-colors w-full dark:[color-scheme:dark];
}
:deep(.form-control-core button > div) {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

:deep(.form-control-core div) {
  width: 100%;
  display: flex;
}
</style>
