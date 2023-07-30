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
    <div class="overflow-auto px-4">
      <ol class="relative border-l border-gray-200 text-base">
        <li
          v-for="event in ticket.data.history"
          :key="event.name"
          class="mb-4 ml-4"
        >
          <Icon
            icon="lucide:dot"
            class="absolute -left-3 h-6 w-6 bg-white text-gray-500"
          />
          <div class="mb-1 font-medium text-gray-900 first-letter:capitalize">
            {{ userStore.getUser(event.owner).full_name }} {{ event.action }}
          </div>
          <Tooltip :text="dayjs(event.creation).format(dateFmtLong)">
            <div class="text-gray-700 first-letter:capitalize">
              {{ dayjs(event.creation).fromNow() }}
            </div>
          </Tooltip>
        </li>
      </ol>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Button, Tooltip } from "frappe-ui";
import dayjs from "dayjs";
import { Icon } from "@iconify/vue";
import { useUserStore } from "@/stores/user";
import { useTicketStore, useTicket } from "./data";

const userStore = useUserStore();
const { sidebar } = useTicketStore();
const ticket = useTicket();
const dateFmtLong = "dddd, MMMM D, YYYY h:mm A";
</script>
