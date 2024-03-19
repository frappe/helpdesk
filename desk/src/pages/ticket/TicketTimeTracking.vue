<template>
  <div class="flex flex-col border-l">
    <TicketSidebarHeader title="Time Tracking" />
    <div class="overflow-auto p-5">
      <ol class="relative border-l border-gray-200 text-base">
        <li v-for="entry in timeEntries" :key="entry.name" class="mb-4 ml-4">
          <TimelineItem :user="entry.agent" :date="entry.start_time" />
          <div>{{ entry.status }} - {{ entry.parentfield }}</div>
        </li>
      </ol>
    </div>
  </div>
</template>

<script>
import { ref, inject, onMounted, computed } from "vue";
import { ITicket } from "./symbols";
import { TimelineItem } from "@/components";

export default {
  setup() {
    const ticket = inject(ITicket); // Inject the ticket object
    const ticketId = computed(() => ticket.data.name); // Access the ticket ID
    const timeEntries = ref([]);

    // Function to fetch time entries
    const fetchTimeEntries = async () => {
      try {
        const response = await fetch(
          "/api/method/helpdesk.helpdesk.doctype.hd_ticket.api.get_time_entries_for_ticket",
          {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
              Accept: "application/json",
              "X-Frappe-CSRF-Token": window.csrf_token,
            },
            body: JSON.stringify({ ticket_id: ticketId.value }), // Use the computed ticket ID
          }
        );
        const data = await response.json();
        if (data.message) {
          timeEntries.value = data.message;
        } else {
          throw new Error("Failed to fetch time entries");
        }
      } catch (error) {
        console.error("Error fetching time entries:", error);
      }
    };

    onMounted(fetchTimeEntries);

    return { timeEntries };
  },
};
</script>
