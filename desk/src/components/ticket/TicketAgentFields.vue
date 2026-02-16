<template>
  <div class="flex flex-1 flex-col overflow-hidden overflow-y-auto border-b">
    <TicketField
      v-for="field in fields"
      :key="field.fieldname"
      :field="field"
      :value="ticket[field.fieldname]"
      @change="(data) => update(data.fieldname, data.value)"
    />
  </div>
</template>

<script setup lang="ts">
import { parseField } from "@/composables/formCustomisation";
import { Field, FieldValue } from "@/types";
import { toast } from "frappe-ui";
import { computed, inject } from "vue";
import TicketField from "../TicketField.vue";
const emit = defineEmits(["update"]);

const props = defineProps({
  ticket: {
    type: Object,
    required: true,
  },
});

const fieldOverrides = inject("fieldOverrides", {});

const fields = computed(
  () =>
    props.ticket?.fields
      ?.map((field: Field) => {
        const parsedField = parseField(field, props.ticket);
        const overrides = fieldOverrides[field.fieldname];

        return overrides
          ? {
              ...parsedField,
              ...overrides,
              filters: overrides.link_filters
                ? JSON.parse(overrides.link_filters)
                : parsedField.filters,
            }
          : parsedField;
      })
      .filter((field) => field.display_via_depends_on) ?? []
);

const customOnChange = computed(() => props.ticket?._customOnChange);

function update(
  fieldname: Field["fieldname"],
  value: FieldValue,
  event = null
) {
  if (fieldname === "subject" && value === "") {
    toast.error("Subject is required");
    if (event?.target) event.target.value = props.ticket.subject;
    return;
  }

  const oldValue = props.ticket[fieldname];
  if (oldValue === value) return;

  const fieldtype = props.ticket.fields?.find(
    (f) => f.fieldname === fieldname
  )?.fieldtype;
  customOnChange.value?.[fieldname]?.forEach((fn: Function) =>
    fn(value, fieldtype)
  );
  emit("update", { field: fieldname, value });
}
</script>
<style scoped>
:deep(.form-control input:not([type="checkbox"])),
:deep(.form-control select),
:deep(.form-control textarea),
:deep(.form-control button) {
  border-color: transparent;
  background: white;
}
:deep(.form-control textarea) {
  field-sizing: content;
}

:deep(.form-control button) {
  gap: 0;
}
:deep(.form-control [type="checkbox"]) {
  margin-left: 9px;
  cursor: pointer;
}

:deep(.form-control button > div) {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

:deep(.form-control button svg) {
  color: white;
  width: 0;
}
</style>
