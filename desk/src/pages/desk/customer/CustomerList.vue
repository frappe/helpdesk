<template>
  <div class="flex flex-col">
    <PageTitle title="Customers">
      <template #right>
        <Button
          label="New customer"
          theme="gray"
          variant="solid"
          @click="isDialogVisible = !isDialogVisible"
        >
          <template #prefix>
            <IconPlus class="h-4 w-4" />
          </template>
        </Button>
      </template>
    </PageTitle>
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
import { usePageMeta, Avatar } from "frappe-ui";
import { createListManager } from "@/composables/listManager";
import NewCustomerDialog from "@/components/desk/global/NewCustomerDialog.vue";
import PageTitle from "@/components/PageTitle.vue";
import { ListView } from "@/components";
import CustomerDialog from "./CustomerDialog.vue";
import IconPlus from "~icons/lucide/plus";

const isDialogVisible = ref(false);
const isCustomerDialogVisible = ref(false);
const selectedCustomer = ref(null);
const emptyMessage = "No Customers Found";
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
</script>
