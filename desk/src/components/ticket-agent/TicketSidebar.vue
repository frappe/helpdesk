<template>
  <Resizer
    class="flex flex-col justify-between border-l px-5 pt-3.5"
    side="right"
  >
    <TabButtons :buttons="tabs" v-model="currentTab" class="tab-buttons mb-1" />
    <div class="flex-1">
      <TicketDetails v-if="currentTab === 'details'" />
      <TicketContactInfo v-else />
    </div>
  </Resizer>
</template>

<script setup lang="ts">
import { useTicket } from "@/composables/useTicket";
import { TabButtons } from "frappe-ui";
import { ref } from "vue";
import Resizer from "../Resizer.vue";
import TicketContactInfo from "./TicketContactInfo.vue";
import TicketDetails from "./TicketDetails.vue";
const props = defineProps({
  ticketId: {
    type: String,
    required: true,
  },
});
const ticket = useTicket(props.ticketId);

const currentTab = ref("details");
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
