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
    <TopSection class="mx-5 mb-3.5" :columns="columns" />
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
import { useFilter } from "@/composables/filter";
import { useOrder } from "@/composables/order";
import { createListManager } from "@/composables/listManager";
import PageTitle from "@/components/PageTitle.vue";
import ListNavigation from "@/components/ListNavigation.vue";
import TicketNew from "@/pages/portal/TicketNew.vue";
import MainTable from "./MainTable.vue";
import TopSection from "./TopSection.vue";
import PresetFilters from "./PresetFilters.vue";

const { getArgs } = useFilter("HD Ticket");
const { get: getOrder } = useOrder();
const showNewDialog = ref(false);
const tickets = createListManager({
  doctype: "HD Ticket",
  pageLength: 20,
  filters: getArgs(),
  orderBy: getOrder(),
  realtime: true,
  auto: true,
  transform: (data) => {
    for (const d of data) {
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

const columns = [
  {
    label: "ID",
    key: "name",
    width: "w-12",
  },
  {
    label: "Subject",
    key: "subject",
    width: "w-96",
  },
  {
    label: "Status",
    key: "status",
    width: "w-24",
  },
  {
    label: "Priority",
    key: "priority",
    width: "w-40",
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
    label: "Type",
    key: "ticket_type",
    width: "w-40",
  },
  {
    label: "Contact",
    key: "contact",
    width: "w-40",
  },
  {
    label: "Due in",
    key: "resolution_by",
    width: "w-40",
  },
  {
    label: "Customer",
    key: "customer",
    width: "w-40",
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
  {
    label: "Source",
    key: "via_customer_portal",
    width: "w-40",
  },
];
</script>
