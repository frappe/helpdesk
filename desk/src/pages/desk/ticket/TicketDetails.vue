<template>
  <div class="flex flex-col">
    <div class="border-l">
      <div class="m-4 text-base">
        <div class="flex items-center justify-between">
          <div class="text-lg font-semibold text-gray-900">Ticket details</div>
          <Button
            icon="x"
            theme="gray"
            variant="ghost"
            @click="sidebar.isExpanded = false"
          />
        </div>
        <div class="my-6 flex flex-col justify-between gap-3.5">
          <div v-if="ticket.doc.customer" class="flex justify-between">
            <div class="text-gray-600">Customer:</div>
            <div class="font-medium text-gray-700">
              {{ ticket.doc.customer }}
            </div>
          </div>
          <div class="flex justify-between">
            <div class="text-gray-600">First Response Due:</div>
            <div class="font-medium text-gray-700">
              {{ firstResponseDue }}
            </div>
          </div>
          <div class="flex items-center justify-between">
            <div class="text-gray-600">Resolution Due:</div>
            <div class="font-medium text-gray-700">
              <span v-if="ticket.doc.resolution_by">
                {{ resolutionDue }}
              </span>
              <Badge
                v-else
                label="Paused"
                size="md"
                variant="subtle"
                theme="green"
              />
            </div>
          </div>
        </div>
      </div>
    </div>
    <div class="divider"></div>
    <div
      class="flex grow flex-col gap-3 truncate border-l p-4"
      :style="{
        'overflow-y': 'scroll',
      }"
    >
      <div class="flex flex-col gap-1">
        <div class="text-xs text-gray-600">Assigned To</div>
        <Autocomplete
          placeholder="Select an agent"
          :options="agentStore.dropdown"
          :value="changeAssignedTo || assignedTo"
          @change="changeAssignedTo = $event"
        />
      </div>
      <div class="flex flex-col gap-1">
        <div class="text-xs text-gray-600">Ticket Type</div>
        <Autocomplete
          v-model="ticket.doc.ticket_type"
          placeholder="Select a ticket type"
          :options="ticketTypeStore.dropdown"
        />
      </div>
      <div class="flex flex-col gap-1">
        <div class="text-xs text-gray-600">Status</div>
        <Autocomplete
          v-model="ticket.doc.status"
          placeholder="Select a status"
          :options="ticketStatusStore.dropdown"
        />
      </div>
      <div class="flex flex-col gap-1">
        <div class="text-xs text-gray-600">Priority</div>
        <Autocomplete
          v-model="ticket.doc.priority"
          placeholder="Select a priority"
          :options="ticketPriorityStore.dropdown"
        />
      </div>
      <div class="flex flex-col gap-1">
        <div class="text-xs text-gray-600">Team</div>
        <Autocomplete
          v-model="ticket.doc.agent_group"
          placeholder="Select a team"
          :options="teamStore.dropdown"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch, Ref } from "vue";
import { Autocomplete, Button } from "frappe-ui";
import dayjs from "dayjs";
import { useAgentStore } from "@/stores/agent";
import { useTeamStore } from "@/stores/team";
import { useTicketPriorityStore } from "@/stores/ticketPriority";
import { useTicketStatusStore } from "@/stores/ticketStatus";
import { useTicketTypeStore } from "@/stores/ticketType";
import { useTicketStore } from "./data";

const agentStore = useAgentStore();
const teamStore = useTeamStore();
const ticketPriorityStore = useTicketPriorityStore();
const ticketStatusStore = useTicketStatusStore();
const ticketTypeStore = useTicketTypeStore();
const { sidebar, ticket } = useTicketStore();

const dateFormat = "MMM D, h:mm A";
const firstResponseDue = computed(() =>
  dayjs(ticket.doc.response_by).format(dateFormat)
);
const resolutionDue = computed(() =>
  dayjs(ticket.doc.resolution_by).format(dateFormat)
);

/**
Fetch assignee info. This is expected to be a list of assigned users, even though we want
only one. This could be considered future proofing.
*/
ticket.getAssignees.fetch();

/**
Last assignee from the list, where expected list length is just one. Transformed into an
object to be used with `Autocomplete`
*/
const assignedTo = computed(() => {
  const assigned = (ticket.getAssignees.data?.message || []).pop();
  return agentStore.dropdown.find((agent) => agent.value === assigned?.name);
});

const changeAssignedTo: Ref = ref(null);

watch(changeAssignedTo, (changed) => {
  ticket.assign.submit({
    agent: changed.value,
  });
});

watch(
  [
    () => ticket.doc.agent_group,
    () => ticket.doc.priority,
    () => ticket.doc.status,
    () => ticket.doc.ticket_type,
  ],
  () => {
    const fields = ["agent_group", "priority", "status", "ticket_type"];
    const isChanged = !!fields.find((f) => ticket.doc[f]?.value);
    if (!isChanged) return;

    const [agent_group, priority, status, ticket_type] = fields.map(
      (f) => ticket.doc[f]?.value || ticket.doc[f]
    );

    ticket.setValue.submit({
      agent_group,
      priority,
      status,
      ticket_type,
    });
  }
);
</script>

<style scoped>
.divider {
  border-bottom: 1px solid #e2e2e2;
  border-style: dashed;
  position: relative;
}

.divider:before {
  position: absolute;
  bottom: -14px;
  left: 0;
  height: 28px;
  width: 14px;
  background: white;
  content: "";
  border-top-right-radius: 9999px;
  border-bottom-right-radius: 9999px;
  border-right-width: 1px;
  border-top-width: 1px;
  border-bottom-width: 1px;
}

.divider:after {
  position: absolute;
  bottom: -14px;
  left: 0;
  height: 28px;
  width: 14px;
  background: white;
  content: "";
  border-top-left-radius: 9999px;
  border-bottom-left-radius: 9999px;
  border-left-width: 1px;
  border-top-width: 1px;
  border-bottom-width: 1px;
}

.divider:after {
  right: 0;
  left: auto;
}
</style>
