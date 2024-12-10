<template>
  <div class="flex flex-1 flex-col overflow-hidden overflow-y-auto border-b">
    <div
      v-for="o in options"
      :key="o.field"
      class="flex items-center gap-2 px-6 pb-1 leading-5 first:mt-3"
    >
      <Tooltip :text="o.label">
        <div class="w-[106px] shrink-0 truncate text-sm text-gray-600">
          {{ o.label }}
        </div>
      </Tooltip>
      <div
        class="-m-0.5 min-h-[28px] flex-1 items-center overflow-hidden p-0.5 text-base"
      >
        <FormControl
          v-if="o.type === 'textarea'"
          class="form-control"
          :type="o.type"
          :value="ticket[o.field]"
          variant="subtle"
          rows="2"
          @change="update(o.field, $event.target.value, $event)"
        />
        <Link
          v-else-if="o.field === 'customer'"
          class="form-control"
          :value="ticket[o.field]"
          :doctype="o.options"
          :placeholder="o.placeholder"
          @change="update(o.field, $event)"
        />
        <Autocomplete
          v-else
          class="form-control"
          :options="o.store.dropdown"
          :placeholder="`Add ${o.label}`"
          :value="ticket[o.field]"
          @change="update(o.field, $event.value)"
        />
      </div>
    </div>
    <UniInput2
      v-for="field in customFields"
      :key="field.fieldname"
      :field="field"
      :value="ticket[field.fieldname]"
      @change="(data) => update(data.fieldname, data.value)"
    />
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { FormControl, Tooltip } from "frappe-ui";
import { Autocomplete, Link } from "@/components";
import { useTeamStore } from "@/stores/team";
import { useTicketPriorityStore } from "@/stores/ticketPriority";
import { useTicketTypeStore } from "@/stores/ticketType";
import UniInput2 from "@/components/UniInput2.vue";
import { createToast } from "@/utils";
import { Field, FieldValue } from "@/types";

const emit = defineEmits(["update"]);

const props = defineProps({
  ticket: {
    type: Object,
    required: true,
  },
});

const options = computed(() => {
  return [
    {
      field: "ticket_type",
      label: "Ticket type",
      store: useTicketTypeStore(),
    },
    {
      field: "priority",
      label: "Priority",
      store: useTicketPriorityStore(),
    },
    {
      field: "agent_group",
      label: "Team",
      store: useTeamStore(),
    },
    {
      field: "customer",
      label: "Customer",
      type: "link",
      options: "HD Customer",
      placeholder: "Select Customer",
    },
  ];
});

const customFields = computed(() => {
  const _custom_fields = props.ticket.template.fields.filter(
    (f) => ["subject", "team", "priority"].indexOf(f.fieldname) === -1
  );

  return _custom_fields;
});

function update(field: Field["fieldname"], value: FieldValue, event = null) {
  if (field === "subject" && value === "") {
    createToast({
      title: "Subject is required",
      icon: "x",
      iconClasses: "text-red-600",
    });
    event.target.value = props.ticket.subject;
    return;
  }
  emit("update", { field, value });
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
