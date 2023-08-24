<template>
  <div class="flex flex-col border-l">
    <TicketSidebarHeader title="Views" />
    <div class="overflow-auto p-5">
      <ol class="relative border-l border-gray-200 text-base">
        <li
          v-for="event in ticket.data.views"
          :key="event.name"
          class="mb-4 ml-4"
        >
          <TimelineItem :user="event.viewed_by" :date="event.creation" />
        </li>
      </ol>
    </div>
  </div>
</template>

<script setup lang="ts">
import { TimelineItem } from "@/components";
import TicketSidebarHeader from "./TicketSidebarHeader.vue";
import { useTicket } from "./data";

const ticket = useTicket();
</script>
