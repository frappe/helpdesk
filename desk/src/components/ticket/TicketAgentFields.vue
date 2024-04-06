<template>
  <div
    class="flex flex-1 flex-col justify-between overflow-hidden overflow-y-auto border-b"
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
import { computed } from "vue";
import { Autocomplete } from "@/components";
import { useTeamStore } from "@/stores/team";
import { useTicketPriorityStore } from "@/stores/ticketPriority";
import { useTicketTypeStore } from "@/stores/ticketType";
import { useTicketAgentStore } from "@/stores/ticketAgent";
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
  useTicketAgentStore().updateTicket(field, value);
  createToast({
    title: "Ticket updated",
    icon: "check",
    iconClasses: "text-green-600",
  });
}
</script>
