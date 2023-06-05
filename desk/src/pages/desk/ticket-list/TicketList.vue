<template>
  <div class="flex flex-col">
    <ListHeader />
    <TopSection />
    <MainTable v-if="tickets.totalCount" class="grow" />
    <div
      v-else
      class="flex grow items-center justify-center text-sm text-gray-800"
    >
      {{ isEmptyMessage }}
    </div>
    <ListNavigation v-bind="tickets" class="p-3" />
  </div>
</template>

<script setup lang="ts">
import { onMounted, onUnmounted } from "vue";
import { useTicketListStore } from "./data";
import ListNavigation from "@/components/ListNavigation.vue";
import ListHeader from "./ListHeader.vue";
import TopSection from "./TopSection.vue";
import MainTable from "./MainTable.vue";

const { init, deinit, tickets } = useTicketListStore();
const isEmptyMessage =
  "🎉 Great news! There are currently no tickets to display. Keep up the good work!";

onMounted(init);
onUnmounted(deinit);
</script>
