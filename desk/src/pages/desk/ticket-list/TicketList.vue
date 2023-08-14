<template>
  <div class="flex flex-col">
    <PageTitle>
      <template #title>
        <PresetFilters doctype="HD Ticket" />
      </template>
      <template #right>
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
      </template>
    </PageTitle>
    <TopSection class="mx-4 mb-3" :columns="columns" />
    <MainTable :tickets="tickets.list?.data" :columns="columns" class="grow" />
    <ListNavigation v-bind="tickets" class="p-2" />
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
import { ref } from "vue";
import { Button, Dialog } from "frappe-ui";
import { Icon } from "@iconify/vue";
import { AGENT_PORTAL_TICKET } from "@/router";
import { socket } from "@/socket";
import { useAuthStore } from "@/stores/auth";
import { useFilter } from "@/composables/filter";
import { useOrder } from "@/composables/order";
import { createListManager } from "@/composables/listManager";
import PageTitle from "@/components/PageTitle.vue";
import ListNavigation from "@/components/ListNavigation.vue";
import TicketNew from "@/pages/portal/TicketNew.vue";
import MainTable from "./MainTable.vue";
import TopSection from "./TopSection.vue";
import PresetFilters from "./PresetFilters.vue";

const { userId } = useAuthStore();
const { getArgs } = useFilter("HD Ticket");
const { get: getOrder } = useOrder();
const showNewDialog = ref(false);
const tickets = createListManager({
  doctype: "HD Ticket",
  pageLength: 20,
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

socket.on("helpdesk:new-ticket", () => {
  if (!tickets.hasPreviousPage) tickets.reload();
});

const columns = [
  {
    label: "Subject",
    key: "subject",
    width: "w-96",
  },
  {
    label: "Status",
    key: "status",
    width: "w-28",
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
    label: "Due in",
    key: "resolution_by",
    width: "w-36",
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
    width: "w-36",
  },
  {
    label: "Created on",
    key: "creation",
    width: "w-36",
  },
];
</script>
