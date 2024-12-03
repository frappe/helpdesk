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
    <!-- View Controls -->
    <div
      v-if="
        !filterableFields.loading &&
        !sortableFields.loading &&
        !quickFilters.loading
      "
      class="flex items-center justify-between gap-2 px-5 pb-4 pt-3"
    >
      <QuickFilters />
      <div class="flex items-center gap-2">
        <Button :label="'Refresh'" @click="reload()" :loading="agents.loading">
          <template #icon>
            <RefreshIcon class="h-4 w-4" />
          </template>
        </Button>
        <Filter />
        <SortBy :hide-label="false" />
      </div>
    </div>
    <div class="flex-1">
      {{ agents?.data?.data }}
    </div>
    <div class="p-20 border-t sm:px-5 px-3 py-2">
      <ListFooter
        :options="{
          rowCount: agents?.data?.row_count,
          totalCount: agents?.data?.total_count,
        }"
        :pageLengthCount="defaultParams.page_length_count"
        @loadMore="handlePageLength(defaultParams.page_length_count, true)"
        v-model="defaultParams.page_length_count"
        @update:modelValue="
          (count) => {
            handlePageLength(count);
          }
        "
      />
    </div>
    <AddNewAgentsDialog
      :show="isDialogVisible"
      @close="isDialogVisible = false"
    />
  </div>
</template>
<script setup lang="ts">
import { reactive, ref, provide } from "vue";
import {
  usePageMeta,
  Avatar,
  Badge,
  createResource,
  ListFooter,
} from "frappe-ui";
import AddNewAgentsDialog from "@/components/desk/global/AddNewAgentsDialog.vue";
import LayoutHeader from "@/components/LayoutHeader.vue";
import { Filter, SortBy, QuickFilters } from "@/components/view-controls";

const isDialogVisible = ref(false);

const defaultParams = reactive({
  doctype: "HD Agent",
  filters: {},
  order_by: "",
  page_length: 20,
  page_length_count: 20,
});

const agents = createResource({
  url: "helpdesk.api.doc.get_list_data",
  params: defaultParams,
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

const quickFilters = createResource({
  url: "helpdesk.api.doc.get_quick_filters",
  auto: true,
  params: {
    doctype: "HD Agent",
  },
});

const listViewData = reactive({
  list: agents,
  filterableFields,
  quickFilters,
  sortableFields,
});

provide("listViewData", listViewData);

provide("listViewActions", {
  applyFilters,
  applySort,
  addColumn,
  reload,
});

function applyFilters(filters) {
  defaultParams.filters = { ...filters };
  agents.submit({ ...defaultParams, filters });
}

function applySort(order_by: string) {
  defaultParams.order_by = order_by;
  agents.submit({ ...defaultParams, order_by });
}

function addColumn(field) {
  console.log("ADD COLUMN", field);
}

function reload() {
  agents.reload({ ...defaultParams });
}

function handlePageLength(count: number, loadMore: boolean = false) {
  if (count >= agents.data.row_count) {
    return;
  }
  defaultParams.page_length_count = count;
  if (loadMore) {
    defaultParams.page_length += count;
  } else {
    if (
      count === defaultParams.page_length &&
      count === defaultParams.page_length_count
    ) {
      return;
    }
    defaultParams.page_length = count;
    defaultParams.page_length_count = count;
  }
  agents.reload();
}

// watch(
//   () => defaultParams.page_length_count,
//   (count) => {
//     handlePageLength(count);
//   }
// );

usePageMeta(() => {
  return {
    title: "Agents",
  };
});
</script>
