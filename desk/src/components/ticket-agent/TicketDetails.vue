<template>
  <div>
    <!-- User avatar with buttons -->
    <TicketContact :contact="ticket?.doc.contact" />

    <!-- 
	Core fields
		- Type (Incident/Request/etc.)
		- Priority (Low/Medium/High)
		- Customer (selected customer)
		- Status (Open/Closed/etc.)
	-->
    <div></div>

    <!-- Assignees -->
    <div></div>

    <!-- End of this section -->

    <!-- Additional Fields -->
    <div></div>
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

<style scoped></style>
