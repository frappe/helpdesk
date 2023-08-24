<template>
  <div class="flex flex-col">
    <PageTitle title="Tickets">
      <template #right>
        <span class="flex gap-2">
          <Button
            label="New ticket"
            theme="gray"
            variant="solid"
            @click="showNewDialog = !showNewDialog"
          >
            <template #prefix>
              <Icon icon="lucide:plus" class="h-4 w-4" />
            </template>
          </Button>
        </span>
      </template>
    </PageTitle>
    <div class="my-2.5 mx-5 flex items-center justify-between">
      <PresetFilters doctype="HD Ticket" />
      <div class="flex items-center gap-2">
        <FilterPopover doctype="HD Ticket" />
        <Dropdown :options="sortOptions">
          <template #default>
            <Button :label="getOrder() || 'Sort'" variant="outline" size="sm">
              <template #prefix>
                <Icon icon="lucide:arrow-down-up" />
              </template>
            </Button>
          </template>
        </Dropdown>
        <ColumnSelector id="ticket" :columns="columns" />
      </div>
    </div>
    <MainTable :tickets="tickets.data" :columns="columns" class="grow" />
    <ListNavigation :resource="tickets" />
    <Dialog v-model="showNewDialog" :options="{ size: '3xl' }">
      <template #body-main>
        <TicketNew
          :hide-back-button="true"
          :hide-about="true"
          :show-hidden-fields="true"
        />
      </template>
    </Dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";
import {
  createResource,
  usePageMeta,
  Button,
  Dialog,
  Dropdown,
} from "frappe-ui";
import { Icon } from "@iconify/vue";
import { AGENT_PORTAL_TICKET } from "@/router";
import { socket } from "@/socket";
import { useAuthStore } from "@/stores/auth";
import { useFilter } from "@/composables/filter";
import { useOrder } from "@/composables/order";
import { createListManager } from "@/composables/listManager";
import ListNavigation from "@/components/ListNavigation.vue";
import PageTitle from "@/components/PageTitle.vue";
import { ColumnSelector, FilterPopover } from "@/components";
import TicketNew from "@/pages/portal/TicketNew.vue";
import MainTable from "./MainTable.vue";
import PresetFilters from "./PresetFilters.vue";

const { userId } = useAuthStore();
const { getArgs } = useFilter("HD Ticket");
const { get: getOrder, set: setOrder } = useOrder();
const showNewDialog = ref(false);
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
    key: "via_customer_portal",
    width: "w-36",
  },
  {
    label: "Assigned to",
    icon: "lucide:user",
    key: "_assign",
    width: "w-8",
    align: "m-auto",
  },
  {
    label: "Count communication",
    icon: "lucide:mail",
    key: "count_communication",
    width: "w-8",
    align: "m-auto",
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
