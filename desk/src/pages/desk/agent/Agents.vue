<template>
  <div class="flex flex-col">
    <LayoutHeader>
      <template #left-header>
        <div class="text-lg font-medium text-gray-900">Agents</div>
      </template>
      <template #right-header>
        <Button
          label="New agent"
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
    <div v-if="!filterableFields.loading">
      <Filter class="w-fit" />
    </div>
    <AddNewAgentsDialog
      :show="isDialogVisible"
      @close="isDialogVisible = false"
    />
  </div>
</template>
<script setup lang="ts">
import { reactive, ref, provide } from "vue";
import { usePageMeta, Avatar, Badge, createResource } from "frappe-ui";
import AddNewAgentsDialog from "@/components/desk/global/AddNewAgentsDialog.vue";
import LayoutHeader from "@/components/LayoutHeader.vue";
import { Filter } from "@/components/view-controls";

const isDialogVisible = ref(false);

const agents = createResource({
  url: "helpdesk.api.doc.get_list_data",
  makeParams: (params) => {
    return {
      doctype: "HD Agent",
      filters: params?.filters,
    };
  },
  auto: true,
});

const filterableFields = createResource({
  url: "helpdesk.api.doc.get_filterable_fields",
  cache: ["DocField", "HD Agent"],
  auto: true,
  params: {
    doctype: "HD Agent",
    append_assign: true,
  },
  transform: (data) => {
    data = data.map((field) => {
      return {
        label: field.label,
        value: field.fieldname,
        ...field,
      };
    });
    listViewData.filterableFields = data;
    return data;
  },
});

const sortableFields = createResource({
  url: "helpdesk.api.doc.sort_options",
  auto: true,
  params: {
    doctype: "HD Agent",
  },
});

const listViewData = reactive({
  list: agents,
  filterableFields,
  sortableFields,
});

provide("listViewData", listViewData);

provide("listViewActions", {
  applyFilters,
  applySort,
  addColumn,
});

function applyFilters(filters) {
  console.log("APPLY FILTER", filters);
  agents.filters = filters;
  agents.submit({ filters });
}

function applySort(field) {
  console.log("APPLY SORT", field);
}

function addColumn(field) {
  console.log("ADD COLUMN", field);
}

usePageMeta(() => {
  return {
    title: "Agents",
  };
});
</script>
