<template>
  <div class="flex flex-col">
    <PageTitle title="Ticket Types">
      <template #right>
        <RouterLink :to="{ name: AGENT_PORTAL_TICKET_TYPE_NEW }">
          <Button
            icon-left="plus"
            label="New ticket type"
            class="bg-gray-900 text-white hover:bg-gray-800"
          />
        </RouterLink>
      </template>
    </PageTitle>
    <HelpdeskTable
      class="grow"
      :columns="columns"
      :data="ticketTypes.list?.data || []"
      row-key="name"
      :emit-row-click="true"
      :hide-checkbox="true"
      :hide-column-selector="true"
      @row-click="gotoTeam"
    />
    <ListNavigation class="p-3" v-bind="ticketTypes" />
  </div>
</template>
<script setup lang="ts">
import { useRouter } from "vue-router";
import {
  AGENT_PORTAL_TICKET_TYPE_NEW,
  AGENT_PORTAL_TICKET_TYPE_SINGLE,
} from "@/router";
import { createListManager } from "@/composables/listManager";
import PageTitle from "@/components/PageTitle.vue";
import HelpdeskTable from "@/components/HelpdeskTable.vue";
import ListNavigation from "@/components/ListNavigation.vue";

const router = useRouter();
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

function gotoTeam(id: string) {
  router.push({
    name: AGENT_PORTAL_TICKET_TYPE_SINGLE,
    params: {
      id,
    },
  });
}
</script>
