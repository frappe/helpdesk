<template>
  <div class="flex flex-col">
    <LayoutHeader>
      <template #left-header>
        <div class="text-lg font-medium text-gray-900">Customers</div>
      </template>
      <template #right-header>
        <Button
          label="New customer"
          theme="gray"
          variant="solid"
          @click="isDialogVisible = !isDialogVisible"
        >
          <template #prefix>
            <LucidePlus class="h-4 w-4" />
          </template>
        </Button>
      </template>
    </LayoutHeader>
    <ListView
      :columns="columns"
      :resource="customers"
      class="mt-2.5"
      doctype="HD Customer"
    >
      <template #name="{ data }">
        <div class="flex items-center gap-2">
          <Avatar :label="data.name" :image="data.image" size="sm" />
          <div class="line-clamp-1">{{ data.name }}</div>
        </div>
      </template>
    </ListView>
    <NewCustomerDialog
      v-model="isDialogVisible"
      @customer-created="handleCustomer"
    />
    <span v-if="isCustomerDialogVisible">
      <CustomerDialog
        v-model="isCustomerDialogVisible"
        :name="selectedCustomer"
        @customer-updated="handleCustomer(true)"
      />
    </span>
  </div>
</template>
<script setup lang="ts">
import { ref } from "vue";
import { usePageMeta, Avatar } from "frappe-ui";
import { createListManager } from "@/composables/listManager";
import NewCustomerDialog from "@/components/desk/global/NewCustomerDialog.vue";
import { ListView } from "@/components";
import CustomerDialog from "./CustomerDialog.vue";
import LayoutHeader from "@/components/LayoutHeader.vue";

const isDialogVisible = ref(false);
const isCustomerDialogVisible = ref(false);
const selectedCustomer = ref(null);
// const emptyMessage = "No Customers Found";
const columns = [
  {
    label: "Name",
    key: "name",
    width: "w-80",
  },
  {
    label: "Domain",
    key: "domain",
    width: "w-80",
  },
];

const customers = createListManager({
  doctype: "HD Customer",
  fields: ["name", "image", "domain"],
  auto: true,
  transform: (data) => {
    for (const d of data) {
      d.onClick = () => openCustomer(d.name);
    }
    return data;
  },
});

usePageMeta(() => {
  return {
    title: "Customers",
  };
});

function openCustomer(id: string) {
  selectedCustomer.value = id;
  isCustomerDialogVisible.value = true;
}
function handleCustomer(updated = false) {
  updated
    ? (isCustomerDialogVisible.value = false)
    : (isDialogVisible.value = false);
  customers.reload();
}
</script>
