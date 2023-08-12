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
    <ListView
      :columns="columns"
      :data="ticketTypes.list?.data || []"
      :empty-message="emptyMessage"
      class="grow"
      row-key="name"
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
import { ListView } from "@/components";
import ListNavigation from "@/components/ListNavigation.vue";
import IconPlus from "~icons/lucide/plus";

const emptyMessage = "No Ticket Types Found";
const columns = [
  {
    label: "Name",
    key: "name",
    width: "w-80",
  },
  {
    label: "Priority",
    key: "priority",
    width: "w-80",
  },
];

const ticketTypes = createListManager({
  doctype: "HD Ticket Type",
  fields: ["name", "priority"],
  auto: true,
  transform: (data) => {
    for (const d of data) {
      d.onClick = {
        name: AGENT_PORTAL_TICKET_TYPE_SINGLE,
        params: {
          id: d.name,
        },
      };
    }
    return data;
  },
});
</script>
