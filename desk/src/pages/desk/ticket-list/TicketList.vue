<template>
  <div class="flex flex-col">
    <PageTitle title="Tickets">
      <template #right>
        <Button
          label="New ticket"
          theme="gray"
          variant="solid"
          @click="isDialogVisible = !isDialogVisible"
        >
          <template #prefix>
            <IconPlus class="h-4 w-4" />
          </template>
        </Button>
      </template>
      <template #bottom>
        <TopSection class="mt-4" />
      </template>
    </PageTitle>
    <MainTable v-if="!isEmpty(tickets.data?.tickets)" class="grow" />
    <div
      v-else
      class="flex grow items-center justify-center text-sm text-gray-800"
    >
      {{ isEmptyMessage }}
    </div>
    <ListNavigation
      :start-from="start"
      :limit="limit"
      :total-count="tickets.data?.count_total"
      :previous="tickets.previous"
      :next="tickets.next"
      :loading="tickets.loading"
      class="p-2"
    />
    <NewTicketDialog
      v-model="isDialogVisible"
      @close="isDialogVisible = false"
    />
  </div>
</template>

<script setup lang="ts">
import { onMounted, onUnmounted, ref } from "vue";
import { Button } from "frappe-ui";
import { isEmpty } from "lodash";
import { useTicketListStore } from "./data";
import PageTitle from "@/components/PageTitle.vue";
import ListNavigation from "@/components/ListNavigation.vue";
import MainTable from "./MainTable.vue";
import NewTicketDialog from "./NewTicketDialog.vue";
import TopSection from "./TopSection.vue";
import IconPlus from "~icons/lucide/plus";
import { storeToRefs } from "pinia";

const ticketListStore = useTicketListStore();
const { tickets, start, limit } = storeToRefs(ticketListStore);
const isDialogVisible = ref(false);
const isEmptyMessage =
  "🎉 Great news! There are currently no tickets to display. Keep up the good work!";

onMounted(ticketListStore.init);
onUnmounted(ticketListStore.deinit);
</script>
