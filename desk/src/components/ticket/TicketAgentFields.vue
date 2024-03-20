<template>
  <div
    class="flex grow flex-col gap-1.5 truncate border-l"
    :style="{
      'overflow-y': 'scroll',
    }"
  >
    <div
      v-for="o in options"
      :key="o.field"
      class="flex items-center gap-2 px-6 pb-1 leading-5 first:mt-3"
    >
      <div class="w-[106px] shrink-0 text-sm text-gray-600">
        {{ o.label }}
      </div>
      <div
        class="grid min-h-[28px] flex-1 items-center overflow-hidden text-base"
      >
        <Autocomplete
          :options="o.store.dropdown"
          :placeholder="`Select a ${o.label}`"
          :value="ticket[o.field]"
        />
      </div>
    </div>
    <UniInput2
      v-for="field in ticket.template.fields"
      :key="field.fieldname"
      :field="field"
      :value="ticket[field.fieldname]"
    />
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { Autocomplete } from "frappe-ui";
import { useTeamStore } from "@/stores/team";
import { useTicketPriorityStore } from "@/stores/ticketPriority";
import { useTicketTypeStore } from "@/stores/ticketType";
import UniInput2 from "@/components/UniInput2.vue";

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
  ];
});

function update(field, value) {
  //   ticket.update(field, value);
}
</script>
