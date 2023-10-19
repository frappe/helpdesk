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
          <Tooltip :text="item.name" placement="left">
            <div
              class="flex h-7 w-7 items-center justify-center rounded-full text-gray-900 transition-all"
              :class="{
                shadow: isExpanded && selected,
                'bg-gray-50': isExpanded && selected,
              }"
              @click="isExpanded = true"
            >
              <component :is="item.icon" class="h-4 w-4" />
            </div>
          </Tooltip>
        </Tab>
      </TabList>
    </TabGroup>
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { Tooltip } from "frappe-ui";
import { TabGroup, TabList, Tab, TabPanels, TabPanel } from "@headlessui/vue";
import TicketActionsTags from "./TicketActionsTags.vue";
import TicketContact from "./TicketContact.vue";
import TicketDetails from "./TicketDetails.vue";
import TicketHistory from "./TicketHistory.vue";
import TicketViews from "./TicketViews.vue";
import LucideContact2 from "~icons/lucide/contact-2";
import LucideHistory from "~icons/lucide/history";
import LucideInfo from "~icons/lucide/info";
import LucidePointer from "~icons/lucide/pointer";
import LucideView from "~icons/lucide/view";

const isExpanded = ref(true);
const items = [
  {
    name: "Details",
    component: TicketDetails,
    icon: LucideInfo,
  },
  {
    name: "Actions & Tags",
    component: TicketActionsTags,
    icon: LucidePointer,
  },
  {
    name: "Contact",
    component: TicketContact,
    icon: LucideContact2,
  },
  {
    name: "History",
    component: TicketHistory,
    icon: LucideHistory,
  },
  {
    name: "Views",
    component: TicketViews,
    icon: LucideView,
  },
];
</script>
