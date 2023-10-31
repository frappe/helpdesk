<template>
  <span class="flex gap-2">
    <Autocomplete
      :options="agentStore.dropdown"
      :value="
        ticket.doc.assignee
          ? {
              label: ticket.doc.assignee.agent_name,
              value: ticket.doc.assignee.user,
            }
          : null
      "
      placeholder="Assign an agent"
      @change="(e) => ticket.assign.submit({ agent: e.value })"
    />
    <Dropdown
      :options="
        ticketStatusStore.options.map((o) => ({
          label: o,
          value: o,
          onClick: () => ticket.setValue.submit({ status: o }),
        }))
      "
    >
      <Button
        :label="ticket.doc.status"
        :theme="ticketStatusStore.colorMap[ticket.doc.status]"
        variant="subtle"
      >
        <template #suffix>
          <LucideChevronDown class="h-4 w-4" />
        </template>
      </Button>
    </Dropdown>
  </span>
</template>

<script setup lang="ts">
import { inject } from "vue";
import { Autocomplete, Button, Dropdown } from "frappe-ui";
import { useAgentStore } from "@/stores/agent";
import { useTicketStatusStore } from "@/stores/ticketStatus";
import { Ticket } from "./symbols";

const ticket = inject(Ticket);
const agentStore = useAgentStore();
const ticketStatusStore = useTicketStatusStore();
</script>
