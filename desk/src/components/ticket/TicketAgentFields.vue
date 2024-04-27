<template>
  <div class="flex flex-1 flex-col overflow-hidden overflow-y-auto border-b">
    <div
      v-for="o in options"
      :key="o.field"
      class="flex items-center gap-2 px-6 pb-1 leading-5 first:mt-3"
    >
      <div class="w-[106px] shrink-0 text-sm text-gray-600">
        {{ o.label }}
      </div>
      <div class="min-h-[28px] flex-1 items-center overflow-hidden text-base">
        <FormControl
          v-if="o.type === 'select'"
          :type="o.type"
          :value="ticket[o.field]"
          :options="customers?.data"
          @change="update(o.field, $event.target.value)"
        />
        <Autocomplete
          v-else
          :options="o.store.dropdown"
          :placeholder="`Add ${o.label}`"
          :value="ticket[o.field]"
          @change="update(o.field, $event.value)"
        />
      </div>
    </div>
    <UniInput2
      v-for="field in ticket.template.fields"
      :key="field.fieldname"
      :field="field"
      :value="ticket[field.fieldname]"
      @change="(data) => update(data.fieldname, data.value)"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, defineEmits } from "vue";
import { createResource, FormControl } from "frappe-ui";
import { Autocomplete } from "@/components";
import { useTeamStore } from "@/stores/team";
import { useTicketPriorityStore } from "@/stores/ticketPriority";
import { useTicketTypeStore } from "@/stores/ticketType";
import UniInput2 from "@/components/UniInput2.vue";

const emit = defineEmits(["update"]);

const props = defineProps({
  ticket: {
    type: Object,
    required: true,
  },
});

const customers = createResource({
  url: "helpdesk.utils.get_customer",
  params: {
    contact: props.ticket.raised_by,
  },
  auto: true,
  transform: (data) => {
    return data.map((d) => ({
      label: d,
      value: d,
    }));
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
      type: "select",
    },
  ];
});

function update(field, value) {
  emit("update", { field, value });
}
</script>
