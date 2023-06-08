<template>
  <div class="flex flex-col">
    <PageTitle title="Customers">
      <template #right>
        <Button
          icon-left="plus"
          label="New customer"
          class="bg-gray-900 text-white hover:bg-gray-800"
          @click="isDialogVisible = !isDialogVisible"
        />
      </template>
    </PageTitle>
    <HelpdeskTable
      class="grow"
      :columns="columns"
      :data="customers.list?.data || []"
      row-key="name"
      :emit-row-click="true"
      :hide-checkbox="true"
      :hide-column-selector="true"
      @row-click="openCustomer"
    >
      <template #name="{ data }">
        <div class="flex items-center gap-2">
          <Avatar :label="data.name" :image-u-r-l="data.image" size="sm" />
          <div class="line-clamp-1">{{ data.name }}</div>
        </div>
      </template>
    </HelpdeskTable>
    <ListNavigation class="p-3" v-bind="customers" />
    <NewCustomerDialog
      v-model="isDialogVisible"
      @close="isDialogVisible = false"
    />
    <span v-if="isCustomerDialogVisible">
      <CustomerDialog
        v-model="isCustomerDialogVisible"
        :name="selectedCustomer"
      />
    </span>
  </div>
</template>
<script setup lang="ts">
import { ref } from "vue";
import { Avatar } from "frappe-ui";
import { createListManager } from "@/composables/listManager";
import NewCustomerDialog from "@/components/desk/global/NewCustomerDialog.vue";
import PageTitle from "@/components/PageTitle.vue";
import HelpdeskTable from "@/components/HelpdeskTable.vue";
import ListNavigation from "@/components/ListNavigation.vue";
import CustomerDialog from "./CustomerDialog.vue";

const isDialogVisible = ref(false);
const isCustomerDialogVisible = ref(false);
const selectedCustomer = ref(null);
const columns = [
  {
    title: "Name",
    colKey: "name",
    colClass: "w-1/3",
  },
  {
    title: "Domain",
    colKey: "domain",
    colClass: "w-1/3",
  },
  {
    title: "Tickets",
    colKey: "ticket_count",
  },
];

const customers = createListManager({
  doctype: "HD Customer",
  fields: ["name", "image", "domain", "ticket_count"],
  auto: true,
});

function openCustomer(id: string) {
  selectedCustomer.value = id;
  isCustomerDialogVisible.value = true;
}
</script>
