<template>
  <span class="flex gap-2">
    <Autocomplete
      :options="agentStore.dropdown"
      :value="
        data.assignee
          ? {
              label: data.assignee.name,
              value: data.assignee.email,
            }
          : null
      "
      placeholder="Assign an agent"
      @change="assignAgent($event.value)"
    >
      <template #prefix>
        <Avatar
          v-if="data.assignee"
          class="mr-2"
          size="sm"
          :label="data.assignee.name"
          :image="data.assignee.image"
        />
      </template>
    </Autocomplete>
    <Dropdown
      :options="
        ticketStatusStore.options.map((o) => ({
          label: o,
          value: o,
          onClick: () => updateTicketStatus(o),
        }))
      "
    >
      <Button
        :label="ticket.data.status"
        :theme="ticketStatusStore.colorMap[ticket.data.status]"
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
import { computed, inject, ref } from "vue";
import { createResource, Avatar, Button, Dropdown } from "frappe-ui";
import { Autocomplete } from "@/components";
import { emitter } from "@/emitter";
import { createToast } from "@/utils";
import { useAgentStore } from "@/stores/agent";
import { useTicketStatusStore } from "@/stores/ticketStatus";
import { useError } from "@/composables/error";
import { ITicket } from "./symbols";

const ticket = inject(ITicket);
const agentStore = useAgentStore();
const ticketStatusStore = useTicketStatusStore();
const data = computed(() => ticket.data);
const desiredStatus = ref("");

function assignAgent(agent: string) {
  createResource({
    url: "run_doc_method",
    params: {
      dt: "HD Ticket",
      dn: data.value.name,
      method: "assign_agent",
      args: {
        agent,
      },
    },
    auto: true,
    onSuccess: () => {
      emitter.emit("update:ticket");
      createToast({
        title: `Ticket assigned to ${agent}`,
        icon: "check",
        iconClasses: "text-green-600",
      });
    },
    onError: useError(),
  });
}

const setValue = createResource({
  url: "frappe.client.set_value",
  auto: false,
  makeParams: (params) => ({
    doctype: "HD Ticket",
    name: data.value.name,
    fieldname: params.field,
    value: params.value,
  }),
  onSuccess: () => {
    emitter.emit("update:ticket");
    createToast({
      title: "Ticket updated",
      icon: "check",
      iconClasses: "text-green-600",
    });
  },
  onError: useError(),
});

function updateTicketStatus(newStatus) {
  desiredStatus.value = newStatus; // Make sure to declare `desiredStatus` appropriately
  if (desiredStatus.value === "Closed" || desiredStatus.value === "Resolved") {
    checkTimeEntries.fetch(); // Trigger the check
  }
}

let checkTimeEntries = createResource({
  url: "helpdesk.helpdesk.doctype.hd_ticket.api.check_unfinished_time_entries", // Assuming this is the correct endpoint
  params: {
    ticket_id: data.value.name,
  },
  auto: false, // Don't fetch automatically; we'll trigger it manually
  onSuccess: (response) => {
    if (response === true) {
      // If there are incomplete time entries
      createToast({
        title:
          "Incomplete time entries are still open. Please complete them before changing the status.",
        icon: "exclamation-circle",
        iconClasses: "text-yellow-500",
      });
    } else {
      // If there are no incomplete time entries, proceed with status update
      setValue.submit({ field: "status", value: desiredStatus.value });
    }
  },
  onError: useError(),
});
</script>
