<template>
  <HelpdeskTable
    v-model:selection="selection"
    :columns="columns"
    :data="tickets"
    :emit-row-click="true"
    :empty-message="emptyMessage"
    row-key="name"
    @row-click="toTicket"
  >
    <template #subject="{ data }">
      <TicketSummary
        class="col-subject"
        :name="data.name"
        :subject="data.subject"
        :communications="data.count_communication"
        :comments="data.count_comment"
        :seen="data._seen"
      />
    </template>
    <template #status="{ data }">
      <Badge
        :label="data.status"
        :theme="ticketStatusStore.colorMapAgent[data.status]"
        variant="subtle"
      />
    </template>
    <template #priority="{ data }">
      <Badge
        :label="data.priority"
        :theme="ticketPriorityStore.colorMap[data.priority]"
        variant="subtle"
      />
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
      {{ dayjs(data.modified).format(dateFormat) }}
    </template>
    <template #via_customer_portal="{ data }">
      {{ data.via_customer_portal ? "Customer Portal" : "Email" }}
    </template>
    <template #row-extra="{ data }">
      <AssignedInfo :assign="data._assign" />
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
              <Icon icon="lucide:plus-circle" class="h-4 w-4" />
            </template>
          </Button>
        </template>
      </Dropdown>
    </template>
  </HelpdeskTable>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { useRouter } from "vue-router";
import { createResource, Badge, Dropdown } from "frappe-ui";
import dayjs from "dayjs";
import { Icon } from "@iconify/vue";
import { AGENT_PORTAL_TICKET } from "@/router";
import { useAgentStore } from "@/stores/agent";
import { useTicketPriorityStore } from "@/stores/ticketPriority";
import { useTicketStatusStore } from "@/stores/ticketStatus";
import { createToast } from "@/utils/toasts";
import { useFilter } from "@/composables/filter";
import HelpdeskTable from "@/components/HelpdeskTable.vue";
import AssignedInfo from "./AssignedInfo.vue";
import TicketSummary from "./TicketSummary.vue";

interface P {
  tickets?: any[];
}

withDefaults(defineProps<P>(), {
  tickets: () => [],
});
const router = useRouter();
const agentStore = useAgentStore();
const ticketPriorityStore = useTicketPriorityStore();
const ticketStatusStore = useTicketStatusStore();
const { storage: filters, apply: applyFilters } = useFilter();
const selection = ref(new Set<string>());
const emptyMessage =
  "🎉 Great news! There are currently no tickets to display. Keep up the good work!";
const dateFormat = "D/M/YYYY h:mm A";
const columns = [
  {
    title: "Subject",
    isTogglable: false,
    colKey: "subject",
    colClass: "col-subject",
  },
  {
    title: "Status",
    isTogglable: false,
    colKey: "status",
    colClass: "w-24",
  },
  {
    title: "Priority",
    isTogglable: false,
    colKey: "priority",
    colClass: "w-24",
  },
  {
    title: "Type",
    isTogglable: false,
    colKey: "ticket_type",
    colClass: "w-20",
  },
  {
    title: "Contact",
    isTogglable: false,
    colKey: "contact",
    colClass: "w-40",
  },
  {
    title: "Due in",
    isTogglable: false,
    colKey: "resolution_by",
    colClass: "w-24",
  },
  {
    title: "Customer",
    isTogglable: true,
    colKey: "customer",
    colClass: "w-40",
  },
  {
    title: "Created on",
    isTogglable: true,
    colKey: "creation",
    colClass: "w-36",
  },
  {
    title: "Last modified",
    isTogglable: true,
    colKey: "modified",
    colClass: "w-36",
  },
  {
    title: "Source",
    isTogglable: true,
    colKey: "via_customer_portal",
    colClass: "w-20",
  },
];

const bulkAssignTicketToAgent = createResource({
  url: "helpdesk.api.ticket.bulk_assign_ticket_to_agent",
  onSuccess: () => {
    createToast({
      title: "Tickets assigned to agent",
      icon: "check",
      iconClasses: "text-green-500",
    });
  },
  onError: () => {
    createToast({
      title: "Unable to assign tickets to agent.",
      icon: "x",
      iconClasses: "text-red-500",
    });
  },
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

function toTicket(ticketId: string) {
  router.push({
    name: AGENT_PORTAL_TICKET,
    params: {
      ticketId,
    },
  });
}
</script>

<style scoped>
:deep(.col-subject) {
  width: 480px;
}
</style>
