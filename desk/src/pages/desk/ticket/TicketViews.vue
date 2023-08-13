<template>
  <div class="flex flex-col border-l">
    <div class="flex items-center justify-between p-4">
      <div class="text-lg font-semibold text-gray-800">Ticket views</div>
      <Button
        icon="x"
        theme="gray"
        variant="ghost"
        @click="sidebar.isExpanded = false"
      />
    </div>
    <div class="overflow-auto px-4">
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
import { Button } from "frappe-ui";
import { TimelineItem } from "@/components";
import { useTicketStore, useTicket } from "./data";

const { sidebar } = useTicketStore();
const ticket = useTicket();
</script>
