<template>
  <div class="flex flex-col">
    <PageTitle title="Tickets">
      <template #right>
        <Button
          label="New ticket"
          theme="gray"
          variant="solid"
          @click="showNewDialog = !showNewDialog"
        >
          <template #prefix>
            <IconPlus class="h-4 w-4" />
          </template>
        </Button>
      </template>
    </PageTitle>
    <TopSection class="mx-5 mb-3.5" />
    <MainTable :tickets="tickets.list?.data" class="grow" />
    <ListNavigation v-bind="tickets" class="p-2" />
    <NewTicketDialog v-model="showNewDialog" @close="showNewDialog = false" />
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { Button } from "frappe-ui";
import { useFilter } from "@/composables/filter";
import { createListManager } from "@/composables/listManager";
import PageTitle from "@/components/PageTitle.vue";
import ListNavigation from "@/components/ListNavigation.vue";
import MainTable from "./MainTable.vue";
import NewTicketDialog from "./NewTicketDialog.vue";
import TopSection from "./TopSection.vue";
import IconPlus from "~icons/lucide/plus";

const { getArgs } = useFilter();
const showNewDialog = ref(false);
const tickets = createListManager({
  doctype: "HD Ticket",
  pageLength: 20,
  filters: getArgs(),
  realtime: true,
  auto: true,
});
</script>
