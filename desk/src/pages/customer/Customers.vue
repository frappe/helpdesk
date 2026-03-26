<template>
  <div class="flex flex-col">
    <LayoutHeader>
      <template #left-header>
        <div class="text-lg font-medium text-gray-900">Customers</div>
      </template>
      <template #right-header>
        <Button
          label="Create"
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
    <ListViewBuilder :options="options" />
    <NewCustomerDialog v-model="isDialogVisible" />
  </div>
</template>
<script setup lang="ts">
import LayoutHeader from "@/components/LayoutHeader.vue";
import ListViewBuilder from "@/components/ListViewBuilder.vue";
import NewCustomerDialog from "@/components/customer/NewCustomerDialog.vue";
import OrganizationsIcon from "@/components/icons/OrganizationsIcon.vue";
import { __ } from "@/translation";
import { Avatar, usePageMeta } from "frappe-ui";
import { computed, h, ref } from "vue";

const isDialogVisible = ref(false);
const listViewRef = ref(null);
// const emptyMessage = "No Customers Found";
const hasActiveFilters = computed(
  () => Object.keys(listViewRef.value?.list?.params?.filters || {}).length > 0
);

const options = computed(() => {
  return {
    doctype: "HD Customer",
    selectable: true,
    showSelectBanner: true,
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
      title: "No customers found",
      description: hasActiveFilters.value
        ? __(
            "No customers found for the applied filters. Try adjusting or clearing your filters."
          )
        : undefined,
      icon: h(OrganizationsIcon, {
        class: "h-10 w-10",
      }),
    },
    rowRoute: {
      name: "Customer",
      prop: "id",
    },
  };
});

usePageMeta(() => {
  return {
    title: "Customers",
  };
});
</script>
