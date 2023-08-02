<template>
  <div class="flex flex-col">
    <PageTitle title="Ticket Types">
      <template #right>
        <RouterLink :to="{ name: AGENT_PORTAL_TICKET_TYPE_NEW }">
          <Button label="New ticket type" theme="gray" variant="solid">
            <template #prefix>
              <IconPlus class="h-4 w-4" />
            </template>
          </Button>
        </RouterLink>
      </template>
    </PageTitle>
    <HelpdeskTable
      class="grow"
      :columns="columns"
      :data="ticketTypes.list?.data || []"
      :empty-message="emptyMessage"
      row-key="name"
      :hide-checkbox="true"
      :hide-column-selector="true"
      :row-click="{
        type: 'link',
        fn: toType,
      }"
    />
    <ListNavigation class="p-3" v-bind="ticketTypes" />
  </div>
</template>
<script setup lang="ts">
import {
  AGENT_PORTAL_TICKET_TYPE_NEW,
  AGENT_PORTAL_TICKET_TYPE_SINGLE,
} from "@/router";
import { createListManager } from "@/composables/listManager";
import PageTitle from "@/components/PageTitle.vue";
import HelpdeskTable from "@/components/HelpdeskTable.vue";
import ListNavigation from "@/components/ListNavigation.vue";
import IconPlus from "~icons/lucide/plus";

const emptyMessage = "No Ticket Types Found";
const columns = [
  {
    title: "Name",
    colKey: "name",
    colClass: "grow",
  },
  {
    title: "Priority",
    colKey: "priority",
    colClass: "w-1/3",
  },
];

const ticketTypes = createListManager({
  doctype: "HD Ticket Type",
  fields: ["name", "priority"],
  auto: true,
});

function toType(id: string) {
  return {
    name: AGENT_PORTAL_TICKET_TYPE_SINGLE,
    params: {
      id,
    },
  };
}
</script>
