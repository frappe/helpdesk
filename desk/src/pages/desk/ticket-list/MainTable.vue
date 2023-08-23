<template>
  <ListView
    id="ticket"
    :columns="columns"
    :data="tickets"
    doctype="HD Ticket"
    :empty-message="emptyMessage"
    row-key="name"
    checkbox
    filter
  >
    <template #status="{ data }">
      <Badge
        :label="data.status"
        :theme="ticketStatusStore.colorMapAgent[data.status]"
        variant="subtle"
      />
    </template>
    <template #_assign="{ data }">
      <AssignedInfo :assign="data._assign" />
    </template>
    <template #agreement_status="{ data }">
      <Badge
        :label="data.agreement_status"
        :theme="slaStatusColorMap[data.agreement_status]"
        variant="outline"
      />
    </template>
    <template #response_by="{ data }">
      <span v-if="data.response_by">
        <Badge
          v-if="
            data.first_responded_on &&
            dayjs(data.first_responded_on).isBefore(data.response_by)
          "
          label="Fulfilled"
          theme="green"
          variant="outline"
        />
        <Badge
          v-else-if="dayjs(data.first_responded_on).isAfter(data.response_by)"
          label="Failed"
          theme="red"
          variant="outline"
        />
        <Tooltip v-else :text="dayjs(data.response_by).long()">
          {{ dayjs(data.response_by).fromNow() }}
        </Tooltip>
      </span>
    </template>
    <template #resolution_by="{ data }">
      <span v-if="data.resolution_by">
        <Badge
          v-if="
            data.resolution_date &&
            dayjs(data.resolution_date).isBefore(data.resolution_by)
          "
          label="Fulfilled"
          theme="green"
          variant="outline"
        />
        <Badge
          v-else-if="dayjs(data.resolution_date).isAfter(data.resolution_by)"
          label="Failed"
          theme="red"
          variant="outline"
        />
        <Tooltip v-else :text="dayjs(data.resolution_by).long()">
          {{ dayjs(data.resolution_by).fromNow() }}
        </Tooltip>
      </span>
    </template>
    <template #creation="{ data }">
      {{ dayjs(data.creation).fromNow() }}
    </template>
    <template #modified="{ data }">
      {{ dayjs(data.modified).fromNow() }}
    </template>
    <template #via_customer_portal="{ data }">
      {{ data.via_customer_portal ? "Customer Portal" : "Email" }}
    </template>
    <template #actions="{ selection: s }">
      <Dropdown :options="assignOpts(s as Set<number>)">
        <template #default>
          <Button
            class="flex cursor-pointer items-center gap-1 text-gray-700"
            label="Assign"
            theme="gray"
            variant="ghost"
          >
            <template #prefix>
              <Icon icon="lucide:user" class="h-4 w-4" />
            </template>
          </Button>
        </template>
      </Dropdown>
    </template>
  </ListView>
</template>

<script setup lang="ts">
import { createResource, Badge, Dropdown, Tooltip } from "frappe-ui";
import { dayjs } from "@/dayjs";
import { Icon } from "@iconify/vue";
import { useAgentStore } from "@/stores/agent";
import { useTicketStatusStore } from "@/stores/ticketStatus";
import { createToast } from "@/utils";
import { useError } from "@/composables/error";
import { ListView } from "@/components";
import AssignedInfo from "./AssignedInfo.vue";

interface P {
  tickets?: any[];
  columns: any[];
}

withDefaults(defineProps<P>(), {
  tickets: () => [],
});
const agentStore = useAgentStore();
const ticketStatusStore = useTicketStatusStore();
const emptyMessage =
  "🎉 Great news! There are currently no tickets to display. Keep up the good work!";
const slaStatusColorMap = {
  Fulfilled: "green",
  Failed: "red",
  "Resolution Due": "orange",
  "First Response Due": "orange",
  Paused: "blue",
};

const bulkAssignTicketToAgent = createResource({
  url: "helpdesk.api.ticket.bulk_assign_ticket_to_agent",
  onSuccess: () => {
    createToast({
      title: "Tickets assigned to agent",
      icon: "check",
      iconClasses: "text-green-500",
    });
  },
  onError: useError({ title: "Unable to assign tickets to agent" }),
});

function assignOpts(selected: Set<number>) {
  return agentStore.options.map((a) => ({
    label: a.agent_name,
    onClick: () =>
      bulkAssignTicketToAgent.submit({
        ticket_ids: Array.from(selected),
        agent_id: a.name,
      }),
  }));
}
</script>
