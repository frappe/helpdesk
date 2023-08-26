<template>
  <div class="flex">
    <TabGroup vertical>
      <TabPanels
        v-if="isExpanded"
        class="h-full"
        :style="{
          width: '310px',
        }"
      >
        <TabPanel v-for="item in items" :key="item.name" class="h-full">
          <component
            :is="item.component"
            class="h-full"
            @close="() => (isExpanded = false)"
          />
        </TabPanel>
      </TabPanels>
      <TabList
        class="sidebar flex flex-col gap-2 border-l"
        :style="{
          width: '50px',
          padding: '16px 12px 0 10px',
        }"
      >
        <Tab v-for="item in items" :key="item.name" v-slot="{ selected }">
          <div
            class="flex h-7 w-7 items-center justify-center rounded-lg text-gray-600"
            :class="{
              'bg-gray-200': isExpanded && selected,
              'text-gray-900': isExpanded && selected,
            }"
            @click="isExpanded = true"
          >
            <Icon :icon="item.icon" class="h-4 w-4" />
          </div>
        </Tab>
      </TabList>
    </TabGroup>
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { TabGroup, TabList, Tab, TabPanels, TabPanel } from "@headlessui/vue";
import { Icon } from "@iconify/vue";
import TicketContact from "./TicketContact.vue";
import TicketDetails from "./TicketDetails.vue";
import TicketHistory from "./TicketHistory.vue";
import TicketViews from "./TicketViews.vue";

const isExpanded = ref(true);
const items = [
  {
    name: "Ticket Details",
    component: TicketDetails,
    icon: "lucide:info",
  },
  {
    name: "Contact Details",
    component: TicketContact,
    icon: "lucide:contact-2",
  },
  {
    name: "Ticket History",
    component: TicketHistory,
    icon: "lucide:history",
  },
  {
    name: "Ticket Views",
    component: TicketViews,
    icon: "lucide:view",
  },
];
</script>
