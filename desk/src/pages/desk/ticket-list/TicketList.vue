<template>
  <div class="flex flex-col">
    <PageTitle title="Tickets">
      <template #right>
        <Button
          icon-left="plus"
          label="New ticket"
          class="bg-gray-900 text-white hover:bg-gray-800"
          @click="isDialogVisible = !isDialogVisible"
        />
      </template>
    </PageTitle>
    <TopSection />
    <MainTable v-if="tickets.totalCount" class="grow" />
    <div
      v-else
      class="flex grow items-center justify-center text-sm text-gray-800"
    >
      {{ isEmptyMessage }}
    </div>
    <ListNavigation v-bind="tickets" class="p-3" />
    <NewTicketDialog
      v-model="isDialogVisible"
      @close="isDialogVisible = false"
    />
  </div>
</template>

<script setup lang="ts">
import { onMounted, onUnmounted, ref } from "vue";
import { useTicketListStore } from "./data";
import PageTitle from "@/components/PageTitle.vue";
import ListNavigation from "@/components/ListNavigation.vue";
import MainTable from "./MainTable.vue";
import NewTicketDialog from "./NewTicketDialog.vue";
import TopSection from "./TopSection.vue";

const { init, deinit, tickets } = useTicketListStore();
const isDialogVisible = ref(false);
const isEmptyMessage =
  "🎉 Great news! There are currently no tickets to display. Keep up the good work!";

onMounted(init);
onUnmounted(deinit);
</script>
