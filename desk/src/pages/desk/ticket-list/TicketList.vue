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
    <MainTable class="grow" />
    <ListNavigation v-bind="tickets" class="p-2" />
    <NewTicketDialog
      v-model="isDialogVisible"
      @close="isDialogVisible = false"
    />
  </div>
</template>

<script setup lang="ts">
import { onMounted, onUnmounted, ref } from "vue";
import { Button } from "frappe-ui";
import { useTicketListStore } from "./data";
import PageTitle from "@/components/PageTitle.vue";
import ListNavigation from "@/components/ListNavigation.vue";
import MainTable from "./MainTable.vue";
import NewTicketDialog from "./NewTicketDialog.vue";
import TopSection from "./TopSection.vue";
import IconPlus from "~icons/lucide/plus";

const { init, deinit, tickets } = useTicketListStore();
const isDialogVisible = ref(false);

onMounted(init);
onUnmounted(deinit);
</script>
