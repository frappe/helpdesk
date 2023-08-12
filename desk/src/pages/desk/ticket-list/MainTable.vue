<template>
  <ListView
    id="ticket"
    :columns="columns"
    :data="tickets"
    :empty-message="emptyMessage"
    row-key="name"
    checkbox
  >
    <template #status="{ data }">
      <Badge
        :label="data.status"
        :theme="ticketStatusStore.colorMapAgent[data.status]"
        variant="subtle"
        size="lg"
        @click.stop.prevent="
          () => {
            storage.clear();
            storage.add({
              fieldname: 'status',
              operator: 'is',
              value: data.status,
            });
            apply();
          }
        "
      />
    </template>
    <template #_assign="{ data }">
      <AssignedInfo :assign="data._assign" />
    </template>
    <template #resolution_by="{ data }">
      <div
        :class="{
          'text-red-700': Date.parse(data.resolution_by) < Date.now(),
        }"
      >
        {{ data.resolution_by ? dayjs(data.resolution_by).fromNow() : "—" }}
      </div>
    </template>
    <template #creation="{ data }">
      {{ dayjs(data.creation).format(dateFormat) }}
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
import { createResource, Badge, Dropdown } from "frappe-ui";
import dayjs from "dayjs";
import { Icon } from "@iconify/vue";
import { useAgentStore } from "@/stores/agent";
import { useTicketStatusStore } from "@/stores/ticketStatus";
import { createToast } from "@/utils/toasts";
import { useFilter } from "@/composables/filter";
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
const { apply, storage } = useFilter("HD Ticket");
const emptyMessage =
  "🎉 Great news! There are currently no tickets to display. Keep up the good work!";
const dateFormat = "D/M/YYYY h:mm A";

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
