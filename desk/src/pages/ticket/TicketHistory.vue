<template>
  <div class="flex flex-col border-l">
    <TicketSidebarHeader title="History" />
    <div class="overflow-auto p-5">
      <ol class="relative border-l border-gray-200 text-base">
        <li v-for="event in history.data" :key="event.name" class="mb-4 ml-4">
          <TimelineItem
            :user="event.owner"
            :date="event.creation"
            :action="event.action"
          />
        </li>
      </ol>
    </div>
  </div>
</template>

<script setup lang="ts">
import { inject } from "vue";
import { createListResource } from "frappe-ui";
import { TimelineItem } from "@/components";
import TicketSidebarHeader from "./TicketSidebarHeader.vue";
import { Id } from "./symbols";

const id = inject(Id);
const history = createListResource({
  doctype: "HD Ticket Activity",
  fields: ["name", "action", "owner", "creation"],
  filters: {
    ticket: id,
  },
  auto: true,
});
</script>
