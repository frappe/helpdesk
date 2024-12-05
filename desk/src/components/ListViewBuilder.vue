<template>
  <div class="flex flex-col flex-1">
    <!-- View Controls -->
    <div
      class="flex items-center justify-between gap-2 px-5 pb-4 pt-3"
      v-if="showViewControls"
    >
      <QuickFilters />
      <div class="flex items-center gap-2">
        <Button :label="'Refresh'" @click="reload()" :loading="list.loading">
          <template #icon>
            <RefreshIcon class="h-4 w-4" />
          </template>
        </Button>
        <Filter :default_filters="defaultParams.filters" />
        <SortBy :hide-label="false" />
      </div>
    </div>

    <!-- List View -->
    <div class="px-5 overflow-scroll flex-1" v-if="!list.loading">
      <slot v-bind="{ list }">
        <ListView
          :columns="list.data?.columns"
          :rows="list.data?.data"
          row-key="email"
          :options="{
            selectable: false,
            showTooltip: true,
            resizeColumn: true,
          }"
        />
      </slot>
    </div>

    <!-- List Footer -->
    <div class="p-20 border-t sm:px-5 px-3 py-2 bottom-0 sticky bg-white">
      <ListFooter
        :options="{
          rowCount: list?.data?.row_count,
          totalCount: list?.data?.total_count,
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
  </div>
</template>

<script setup lang="ts">
import { reactive, provide, computed } from "vue";
import { createResource, ListView, ListFooter } from "frappe-ui";

import { Filter, SortBy, QuickFilters } from "@/components/view-controls";

const props = defineProps({
  doctype: {
    type: String,
    required: true,
  },
  default_filters: {
    type: Object,
    required: false,
    default: {},
  },
});

const defaultParams = reactive({
  doctype: props.doctype,
  filters: props.default_filters,
  order_by: "",
  page_length: 20,
  page_length_count: 20,
});

const list = createResource({
  url: "helpdesk.api.doc.get_list_data",
  params: defaultParams,
  auto: true,
  onSuccess: (data) => {
    list.params = defaultParams;
  },
});

const filterableFields = createResource({
  url: "helpdesk.api.doc.get_filterable_fields",
  cache: ["DocField", props.doctype],
  auto: true,
  params: {
    doctype: props.doctype,
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
    return data;
  },
});

const sortableFields = createResource({
  url: "helpdesk.api.doc.sort_options",
  auto: true,
  params: {
    doctype: props.doctype,
  },
});

const quickFilters = createResource({
  url: "helpdesk.api.doc.get_quick_filters",
  auto: true,
  params: {
    doctype: props.doctype,
  },
});

const showViewControls = computed(() => {
  return filterableFields.data && sortableFields.data && quickFilters.data;
});

const listViewData = reactive({
  list,
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
  list.submit({ ...defaultParams, filters });
}

function applySort(order_by: string) {
  defaultParams.order_by = order_by;
  list.submit({ ...defaultParams, order_by });
}

function addColumn(field) {
  console.log("ADD COLUMN", field);
}

function reload() {
  list.reload({ ...defaultParams });
}

function handlePageLength(count: number, loadMore: boolean = false) {
  if (count >= list.data?.total_count) {
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
  list.reload();
}
</script>

<style lang="scss" scoped></style>
