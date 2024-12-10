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
    <ListViewBuilder
      ref="listViewRef"
      :options="options"
      @row-click="openCustomer"
      @empty-state-action="isDialogVisible = true"
    />
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
import { ref, computed, h } from "vue";
import { usePageMeta, Avatar } from "frappe-ui";
import NewCustomerDialog from "@/components/desk/global/NewCustomerDialog.vue";
import CustomerDialog from "./CustomerDialog.vue";
import LayoutHeader from "@/components/LayoutHeader.vue";
import ListViewBuilder from "@/components/ListViewBuilder.vue";
import PhoneIcon from "@/components/icons/PhoneIcon.vue";

const isDialogVisible = ref(false);
const isCustomerDialogVisible = ref(false);
const selectedCustomer = ref(null);
const listViewRef = ref(null);
// const emptyMessage = "No Customers Found";

function openCustomer(id: string) {
  selectedCustomer.value = id;
  isCustomerDialogVisible.value = true;
}
function handleCustomer(updated = false) {
  updated
    ? (isCustomerDialogVisible.value = false)
    : (isDialogVisible.value = false);
  listViewRef.value?.reload();
}

const options = computed(() => {
  return {
    doctype: "HD Customer",
    columnConfig: {
      name: {
        prefix: ({ row }) => {
          return h(Avatar, {
            shape: "circle",
            image: row.image,
            label: row.name,
            size: "sm",
          });
        },
      },
    },
    emptyState: {
      title: "No Customers Found",
    },
  };
});

usePageMeta(() => {
  return {
    title: "Customers",
  };
});
</script>
