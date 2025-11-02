<template>
  <div class="flex gap-5 w-full">
    <FormControl
      type="autocomplete"
      label="Default ticket status"
      :options="openStatuses"
      class="flex-1"
      v-model="slaData.default_ticket_status"
    />
    <FormControl
      type="autocomplete"
      label="Ticket reopen status"
      :options="openStatuses"
      class="flex-1"
      v-model="slaData.reopen_ticket_status"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, ComputedRef } from "vue";
import { slaData } from "@/stores/sla";
import { useTicketStatusStore } from "@/stores/ticketStatus";
import { HDTicketStatus } from "@/types/doctypes";

const { statuses } = useTicketStatusStore();

const openStatuses: ComputedRef<HDTicketStatus[]> = computed(() => {
  return statuses.data
    .filter((s: HDTicketStatus) => s.category === "Open")
    .map((s: HDTicketStatus) => {
      return {
        label: s.label_agent,
        value: s.label_agent,
      };
    });
});
</script>
