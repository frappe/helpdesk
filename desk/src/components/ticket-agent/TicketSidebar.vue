<template>
  <Resizer class="flex flex-col justify-between border-l pt-3.5" side="right">
    <TabButtons
      :buttons="tabs"
      v-model="currentTab"
      class="tab-buttons mb-1 px-5"
    />
    <div class="flex-1">
      <TicketDetailsTab v-if="currentTab === 'details'" :ticket-id="ticketId" />
      <TicketContactTab v-else :ticket-id="ticketId" />
    </div>
  </Resizer>
</template>

<script setup lang="ts">
import { useTicket } from "@/composables/useTicket";
import { TabButtons } from "frappe-ui";
import { ref } from "vue";
import Resizer from "../Resizer.vue";
import TicketContactTab from "./TicketContactTab.vue";
import TicketDetailsTab from "./TicketDetailsTab.vue";
const props = defineProps({
  ticketId: {
    type: String,
    required: true,
  },
});
const ticket = useTicket(props.ticketId);

const currentTab = ref("contact");
const tabs = [
  {
    label: "Details",
    value: "details",
  },
  {
    label: "Contact",
    value: "contact",
  },
];
</script>

<style>
.tab-buttons div,
.tab-buttons button {
  width: 100%;
  flex: 1;
}
</style>
