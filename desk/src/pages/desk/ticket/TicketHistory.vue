<template>
  <div class="flex flex-col border-l">
    <div class="flex items-center justify-between p-4">
      <div class="text-lg font-semibold text-gray-800">Ticket history</div>
      <Button
        icon="x"
        theme="gray"
        variant="ghost"
        @click="sidebar.isExpanded = false"
      />
    </div>
    <TabButtons v-model="activeTab" class="mx-auto mb-6" :buttons="tabs" />
    <div class="overflow-auto px-4">
      <ol class="relative border-l border-gray-200 text-base">
        <li v-for="event in source" :key="event.name" class="mb-4 ml-4">
          <TicketHistoryItem
            :user="event['owner'] || event['viewed_by']"
            :date="event.creation"
            :action="event['action']"
          />
        </li>
      </ol>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";
import { Button, TabButtons } from "frappe-ui";
import TicketHistoryItem from "./TicketHistoryItem.vue";
import { useTicketStore, useTicket } from "./data";

const { sidebar } = useTicketStore();
const ticket = useTicket();
const tabs = [{ label: "Actions" }, { label: "Views" }];
const activeTab = ref("Actions");
const source = computed(() =>
  activeTab.value === "Actions"
    ? ticket.value.data.history
    : ticket.value.data.views
);
</script>
