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
      @row-click="goToCustomer"
    />
    <ListNavigation class="p-3" v-bind="customers" />
    <NewCustomerDialog
      v-model="isDialogVisible"
      @close="isDialogVisible = false"
    />
  </div>
</template>
<script setup lang="ts">
import { ref } from "vue";
import { useRouter } from "vue-router";
import { AGENT_PORTAL_CUSTOMER } from "@/router";
import { createListManager } from "@/composables/listManager";
import NewCustomerDialog from "@/components/desk/global/NewCustomerDialog.vue";
import PageTitle from "@/components/PageTitle.vue";
import HelpdeskTable from "@/components/HelpdeskTable.vue";
import ListNavigation from "@/components/ListNavigation.vue";

const router = useRouter();
const isDialogVisible = ref(false);
const columns = [
  {
    title: "Name",
    isTogglable: false,
    colKey: "name",
    colClass: "w-1/2",
  },
];

const customers = createListManager({
  doctype: "HD Customer",
  fields: ["name"],
  auto: true,
});

function goToCustomer(id: string) {
  router.push({
    name: AGENT_PORTAL_CUSTOMER,
    params: {
      id,
    },
  });
}
</script>
