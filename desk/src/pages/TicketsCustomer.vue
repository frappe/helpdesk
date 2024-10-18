<template>
  <div class="flex flex-col">
    <LayoutHeader>
      <template #left-header>
        <Breadcrumbs :items="breadcrumbs" />
      </template>
      <template #right-header>
        <RouterLink :to="{ name: 'TicketNew' }">
          <Button label="New Ticket" theme="gray" variant="solid">
            <template #prefix>
              <LucidePlus class="h-4 w-4" />
            </template>
          </Button>
        </RouterLink>
      </template>
    </LayoutHeader>
    <ListView
      :columns="columns"
      :resource="tickets"
      class="mt-2.5"
      doctype="HD Ticket"
    >
      <template #status="{ data }">
        <Badge
          :label="transformStatus(data.status)"
          :theme="ticketStatusStore.colorMap[data.status]"
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
            {{ dayjs.tz(data.response_by).fromNow() }}
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
            {{ dayjs.tz(data.resolution_by).fromNow() }}
          </Tooltip>
        </span>
      </template>
      <template #creation="{ data }">
        {{ dayjs.tz(data.creation).fromNow() }}
      </template>
    </ListView>
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { Dropdown, Tooltip, Breadcrumbs } from "frappe-ui";
import { dayjs } from "@/dayjs";
import { useConfigStore } from "@/stores/config";
import { useTicketStatusStore } from "@/stores/ticketStatus";
import { createListManager } from "@/composables/listManager";
import { CUSTOMER_PORTAL_TICKET } from "@/router";
import { ListView } from "@/components";
import { ViewControls, LayoutHeader } from "@/components";
const configStore = useConfigStore();
const ticketStatusStore = useTicketStatusStore();
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
    width: "w-32",
  },
  {
    label: "Priority",
    key: "priority",
    width: "w-32",
  },
  {
    label: "First Response",
    key: "response_by",
    width: "w-32",
  },
  {
    label: "Resolution",
    key: "resolution_by",
    width: "w-32",
  },
  {
    label: "Created",
    key: "creation",
    width: "w-32",
  },
];

const tickets = createListManager({
  doctype: "HD Ticket",
  pageLength: 20,
  fields: [
    "name",
    "creation",
    "subject",
    "status",
    "priority",
    "response_by",
    "resolution_by",
    "first_responded_on",
    "resolution_date",
  ],
  auto: true,
  transform: (data) => {
    for (const d of data) {
      d.onClick = {
        name: CUSTOMER_PORTAL_TICKET,
        params: {
          ticketId: d.name,
        },
      };
    }
  },
});

const breadcrumbs = [{ label: "Tickets", route: { name: "TicketsCustomer" } }];

const ACTIVE_TICKET_TYPES = ["Open", "Replied"];
const dropdownTitle = ref("All tickets");
const dropdownOptions = [
  {
    label: "All tickets",
    onClick() {
      filter("All tickets", { status: undefined });
    },
  },
  {
    label: "Open tickets",
    onClick() {
      filter("Open tickets", { status: ["in", ACTIVE_TICKET_TYPES] });
    },
  },
  {
    label: "Closed tickets",
    onClick() {
      filter("Closed tickets", { status: ["not in", ACTIVE_TICKET_TYPES] });
    },
  },
];

// eslint-disable-next-line @typescript-eslint/no-explicit-any
function filter(title: string, filters: Record<string, any>) {
  tickets.update({
    ...tickets,
    filters: {
      ...tickets.filters,
      ...filters,
    },
  });
  tickets.reload();
  dropdownTitle.value = title;
}

function transformStatus(status: string) {
  switch (status) {
    case "Replied":
      return "Awaiting reply";
    default:
      return status;
  }
}
</script>
