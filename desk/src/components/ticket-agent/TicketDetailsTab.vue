<template>
  <div>
    <div class="px-5 border-b pb-4">
      <!-- User avatar with buttons -->
      <TicketContact :contact="ticket?.doc.contact" />
      <!-- Core Fields -->
      <div class="">
        <div class="flex gap-2 items-center w-full mb-2">
          <!-- 2 link fields -->
          <Link
            class="form-control flex-1"
            doctype="HD Ticket Type"
            placeholder="Select Type"
            v-model="ticket.doc.ticket_type"
            label="Type"
            :page-length="10"
          />
          <Link
            class="form-control flex-1"
            doctype="HD Ticket Priority"
            placeholder="Select Priority"
            v-model="ticket.doc.priority"
            label="Priority"
            :page-length="10"
          />
        </div>
        <!-- 1 link field customer -->
        <Link
          class="form-control w-full mb-2"
          doctype="HD Customer"
          placeholder="Select Customer"
          v-model="ticket.doc.customer"
          label="Customer"
          :page-length="10"
        />

        <!-- 1 link field Team -->
        <Link
          class="form-control w-full mb-2"
          doctype="HD Team"
          placeholder="Select Team"
          v-model="ticket.doc.agent_group"
          label="Team"
          :page-length="10"
        />

        <Link
          class="form-control w-full mb-2"
          doctype="HD Team"
          placeholder="Select Team"
          v-model="ticket.doc.raised_by"
          label="Assignee"
          :page-length="10"
        />
      </div>
    </div>

    <!-- Additional Fields -->
    <div>asds</div>
  </div>
</template>

<script setup lang="ts">
import { useTicket } from "@/composables/useTicket";
import TicketContact from "./TicketContact.vue";

const props = defineProps({
  ticketId: {
    type: String,
    required: true,
  },
});
const ticket = useTicket(props.ticketId);
</script>

<style scoped>
:deep(.form-control button) {
  @apply text-base rounded h-7 py-1.5 border border-outline-gray-2 bg-surface-white placeholder-ink-gray-4 hover:border-outline-gray-3 hover:shadow-sm focus:bg-surface-white focus:border-outline-gray-4 focus:shadow-sm focus:ring-0 focus-visible:ring-0 text-ink-gray-8 transition-colors w-full dark:[color-scheme:dark];
}
:deep(.form-control button > div) {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

:deep(.form-control div) {
  width: 100%;
  display: flex;
}
</style>
