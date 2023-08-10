<template>
  <div class="flex flex-col">
    <PageTitle>
      <template #title>
        <PresetFilters doctype="HD Ticket" />
      </template>
      <template #right>
        <Button
          label="New ticket"
          theme="gray"
          variant="solid"
          @click="showNewDialog = !showNewDialog"
        >
          <template #prefix>
            <Icon icon="lucide:plus" class="h-4 w-4" />
          </template>
        </Button>
      </template>
    </PageTitle>
    <TopSection class="mx-5 mb-3.5" />
    <MainTable :tickets="tickets.list?.data" class="grow" />
    <ListNavigation v-bind="tickets" class="p-2" />
    <Dialog v-model="showNewDialog" :options="{ size: '3xl' }">
      <template #body-main>
        <TicketNew
          :hide-back-button="true"
          :hide-about="true"
          :show-hidden-fields="true"
        />
      </template>
    </Dialog>
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { Button, Dialog } from "frappe-ui";
import { Icon } from "@iconify/vue";
import { useFilter } from "@/composables/filter";
import { useOrder } from "@/composables/order";
import { createListManager } from "@/composables/listManager";
import PageTitle from "@/components/PageTitle.vue";
import ListNavigation from "@/components/ListNavigation.vue";
import TicketNew from "@/pages/portal/TicketNew.vue";
import MainTable from "./MainTable.vue";
import TopSection from "./TopSection.vue";
import PresetFilters from "./PresetFilters.vue";

const { getArgs } = useFilter("HD Ticket");
const { get: getOrder } = useOrder();
const showNewDialog = ref(false);
const tickets = createListManager({
  doctype: "HD Ticket",
  pageLength: 20,
  filters: getArgs(),
  orderBy: getOrder(),
  realtime: true,
  auto: true,
});
</script>
