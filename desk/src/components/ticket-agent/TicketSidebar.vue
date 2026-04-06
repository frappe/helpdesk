<template>
  <Resizer class="border-l h-full" side="right">
    <div class="flex flex-col h-full overflow-hidden">
      <TabButtons
        :buttons="tabs"
        v-model="currentTab"
        class="tab-buttons mb-1 px-5 mt-3.5 shrink-0"
      />
      <div class="flex-1 min-h-0">
        <TicketDetailsTab v-if="currentTab === 'details'" />
        <TicketContactTab v-else />
      </div>
    </div>
  </Resizer>
</template>

<script setup lang="ts">
import { TabButtons } from "frappe-ui";
import { ref } from "vue";
import Resizer from "../Resizer.vue";
import TicketContactTab from "./TicketContactTab.vue";
import TicketDetailsTab from "./TicketDetailsTab.vue";

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
