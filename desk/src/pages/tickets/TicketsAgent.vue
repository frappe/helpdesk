<template>
  <div class="flex flex-col">
    <PageTitle title="Tickets">
      <template #right>
        <RouterLink :to="{ name: 'TicketAgentNew' }">
          <Button label="New ticket" theme="gray" variant="solid">
            <template #prefix>
              <LucidePlus class="h-4 w-4" />
            </template>
          </Button>
        </RouterLink>
      </template>
    </PageTitle>
    <div class="mx-5 mt-2.5 flex items-center justify-between">
      <PresetFilters doctype="HD Ticket" />
      <div class="flex items-center gap-2">
        <FilterPopover doctype="HD Ticket" />
        <Dropdown :options="sortOptions">
          <template #default>
            <Button :label="getOrder() || 'Sort'" variant="outline" size="sm">
              <template #prefix>
                <LucideArrowDownUp class="h-4 w-4" />
              </template>
            </Button>
          </template>
        </Dropdown>
        <ColumnSelector doctype="HD Ticket" :columns="columns" />
      </div>
    </div>
    <TicketsAgentList :resource="tickets" :columns="columns" />
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";
import { createResource, usePageMeta, Button, Dropdown } from "frappe-ui";
import { AGENT_PORTAL_TICKET } from "@/router";
import { socket } from "@/socket";
import { useAuthStore } from "@/stores/auth";
import { useFilter } from "@/composables/filter";
import { useOrder } from "@/composables/order";
import { createListManager } from "@/composables/listManager";
import PageTitle from "@/components/PageTitle.vue";
import { ColumnSelector, FilterPopover } from "@/components";
import TicketsAgentList from "./TicketsAgentList.vue";
import PresetFilters from "./PresetFilters.vue";

const { userId } = useAuthStore();
const { getArgs } = useFilter("HD Ticket");
const { get: getOrder, set: setOrder } = useOrder();
const pageLength = ref(20);
const tickets = createListManager({
  doctype: "HD Ticket",
  pageLength: pageLength.value,
  filters: getArgs(),
  orderBy: getOrder(),
  auto: true,
  transform: (data) => {
    for (const d of data) {
      d.class = {
        "font-medium": !d._seen?.includes(userId),
      };
      d.onClick = {
        name: AGENT_PORTAL_TICKET,
        params: {
          ticketId: d.name,
        },
      };
      d.conversation = {
        incoming: d.count_msg_incoming,
        outgoing: d.count_msg_outgoing,
        comments: d.count_comment,
      };
      d.source = d.via_customer_portal ? "Customer portal" : "Email";
    }
    return data;
  },
});

const sortOptionsRes = createResource({
  url: "helpdesk.extends.doc.sort_options",
  auto: true,
  params: {
    doctype: "HD Ticket",
  },
});
const sortOptions = computed(() => {
  return sortOptionsRes.data?.map((o) => ({
    label: o,
    onClick: () => setOrder(o),
  }));
});

socket.on("helpdesk:new-ticket", () => {
  if (!tickets.hasPreviousPage) tickets.reload();
});

const columns = [
  {
    label: "#",
    key: "name",
    width: "w-10",
    text: "text-sm",
  },
  {
    label: "Subject",
    key: "subject",
    width: "w-96",
    text: "text-gray-900",
  },
  {
    label: "Status",
    key: "status",
    width: "w-20",
  },
  {
    label: "Priority",
    key: "priority",
    width: "w-32",
  },
  {
    label: "Type",
    key: "ticket_type",
    width: "w-36",
  },
  {
    label: "Team",
    key: "agent_group",
    width: "w-36",
  },
  {
    label: "Contact",
    key: "contact",
    width: "w-36",
  },
  {
    label: "Agreement status",
    key: "agreement_status",
    width: "w-36",
  },
  {
    label: "First response",
    key: "response_by",
    width: "w-32",
  },
  {
    label: "Resolution",
    key: "resolution_by",
    width: "w-32",
  },
  {
    label: "Customer",
    key: "customer",
    width: "w-36",
  },
  {
    label: "Source",
    key: "source",
    width: "w-36",
  },
  {
    label: "Assignee",
    key: "assignee",
    width: "w-40",
  },
  {
    label: "Conversation",
    key: "conversation",
    width: "w-28",
  },
  {
    label: "Last modified",
    key: "modified",
    width: "w-32",
  },
  {
    label: "Created",
    key: "creation",
    width: "w-36",
  },
];

usePageMeta(() => {
  return {
    title: "Tickets",
  };
});
</script>
