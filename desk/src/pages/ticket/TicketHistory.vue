<template>
  <div class="flex flex-col border-l">
    <TicketSidebarHeader title="History" />
    <div class="overflow-auto p-5">
      <ol class="relative border-l border-gray-200 text-base">
        <li
          v-for="event in ticket.data.history"
          :key="event.name"
          class="mb-4 ml-4"
        >
          <TimelineItem
            :user="event.user"
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
import { TimelineItem } from "@/components";
import TicketSidebarHeader from "./TicketSidebarHeader.vue";
import { ITicket } from "./symbols";

const ticket = inject(ITicket);
</script>
