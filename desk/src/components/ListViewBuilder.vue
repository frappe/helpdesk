<template>
  <!-- View Controls -->
  <FadedScrollableDiv
    class="flex items-center justify-between gap-2 px-5 pb-4 pt-3"
    v-if="showViewControls"
    orientation="horizontal"
  >
    <QuickFilters v-if="!isMobileView" />
    <div class="flex items-center gap-2" v-if="!isMobileView">
      <Reload @click="reload" :loding="list.loading" />
      <Filter :default_filters="defaultParams.filters" />
      <SortBy :hide-label="isMobileView" />
    </div>
    <div v-else class="flex justify-between items-center w-full">
      <Filter :default_filters="defaultParams.filters" />
      <div class="flex items-center gap-2">
        <Reload @click="reload" :loding="list.loading" />
        <SortBy :hide-label="isMobileView" />
      </div>
    </div>
  </FadedScrollableDiv>

  <!-- List View -->
  <slot v-bind="{ list }">
    <ListView
      v-if="list.data?.data.length > 0"
      class="flex-1"
      :columns="columns"
      :rows="rows"
      row-key="name"
      :options="{
        selectable: props.options.selectable ?? true ,
        showTooltip: true,
        resizeColumn: false,
        onRowClick: (row: Object) => emit('rowClick', row['name']),
        emptyState,
      }"
    >
      <ListHeader class="sm:mx-5 mx-3">
        <ListHeaderItem
          v-for="column in columns"
          :key="column.key"
          :item="column"
          @columnWidthUpdated="(width) => console.log(width)"
        />
      </ListHeader>
      <ListRows class="sm:mx-5 mx-3">
        <ListRow
          v-for="row in rows"
          :key="row.name"
          v-slot="{ idx, column, item }"
          :row="row"
          class="truncate text-base"
        >
          <ListRowItem :item="item" :row="row" :column="column">
            <!-- TODO: filters on click of other columns -->
            <!-- and not on first column, it should emit the event -->
            <div v-if="idx === 0" class="truncate">
              {{ item }}
            </div>
            <div v-else-if="column.type === 'Datetime'">
              {{ dayjs.tz(item).fromNow() }}
            </div>
            <div v-else-if="column.type === 'status'">
              <Badge v-bind="handleStatusColor(item)" />
            </div>
            <div v-else class="truncate">
              {{ item }}
            </div>
          </ListRowItem>
        </ListRow>
      </ListRows>
    </ListView>
  </slot>

  <!-- List Footer -->
  <div
    class="p-20 border-t sm:px-5 px-3 py-2"
    v-if="list.data?.data.length > 0"
  >
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
  <!-- Empty State -->
  <EmptyState
    v-else
    :title="emptyState.title"
    @emptyStateAction="emit('emptyStateAction')"
  />
</template>

<script setup lang="ts">
import { reactive, provide, computed } from "vue";
import {
  createResource,
  ListView,
  ListFooter,
  ListRowItem,
  ListRows,
  ListRow,
  ListHeader,
  ListHeaderItem,
  Badge,
} from "frappe-ui";

import { Filter, SortBy, QuickFilters } from "@/components/view-controls";
import { dayjs } from "@/dayjs";
import FadedScrollableDiv from "./FadedScrollableDiv.vue";
import Reload from "./view-controls/Reload.vue";
import { useScreenSize } from "@/composables/screen";
import EmptyState from "./EmptyState.vue";
import { BadgeStatus } from "@/types";

interface P {
  options: {
    doctype: string;
    defaultFilters?: Record<string, any>;
    columnConfig?: Record<string, any>;
    emptyState?: {
      icon?: HTMLElement | string;
      title: string;
    };
    hideViewControls?: boolean;
    selectable?: boolean;
    statusMap?: Record<string, BadgeStatus>;
  };
}

interface E {
  (event: "emptyStateAction"): void;
  (event: "rowClick", row: any): void;
}

const props = withDefaults(defineProps<P>(), {
  options: () => {
    return {
      doctype: "",
      hideViewControls: false,
      selectable: true,
    };
  },
});

const emit = defineEmits<E>();
const { isMobileView } = useScreenSize();
const defaultEmptyState = {
  icon: "",
  title: "No Data Found",
};

const defaultParams = reactive({
  doctype: props.options.doctype,
  filters: props.options.defaultFilters || {},
  order_by: "modified desc",
  page_length: 20,
  page_length_count: 20,
});

const emptyState = computed(() => {
  return props.options?.emptyState || defaultEmptyState;
});

const list = createResource({
  url: "helpdesk.api.doc.get_list_data",
  params: defaultParams,
  auto: true,
  transform: (data) => {
    data.columns.forEach((column) => {
      handleFetchFromField(column);
      handleColumnConfig(column);
    });
    return data;
  },
  onSuccess: () => {
    list.params = defaultParams;
  },
});

const rows = computed(() => list.data?.data);
const columns = computed(() => list.data?.columns);

function handleFetchFromField(column) {
  if (!column.hasOwnProperty("key")) return column;
  const regex = /([a-zA-Z0-9_]+)\.([a-zA-Z0-9_]+)/;
  const isFetchFromField = column.key.match(regex);
  column.key = isFetchFromField ? isFetchFromField[2] : column.key;
}

function handleColumnConfig(column) {
  if (!props.options?.columnConfig) return column;
  const columnConfig = props.options.columnConfig;
  if (!columnConfig.hasOwnProperty(column.key)) return column;
  column.prefix = columnConfig[column.key]?.prefix;

  return column;
}

const statusMap: Record<string, BadgeStatus> = props.options
  .statusMap as Record<string, BadgeStatus>;
function handleStatusColor(status: "Published" | "Draft"): BadgeStatus {
  if (!statusMap)
    return {
      label: status,
      theme: "gray",
    };
  return statusMap[status];
}

const filterableFields = createResource({
  url: "helpdesk.api.doc.get_filterable_fields",
  cache: ["DocField", props.options.doctype],
  auto: !props.options.hideViewControls,
  params: {
    doctype: props.options.doctype,
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
  auto: !props.options.hideViewControls,
  params: {
    doctype: props.options.doctype,
  },
});

const quickFilters = createResource({
  url: "helpdesk.api.doc.get_quick_filters",
  auto: !props.options.hideViewControls,
  params: {
    doctype: props.options.doctype,
  },
  transform: (data) => {
    if (Boolean(data.length)) return;
    data = [{ name: "name", label: "Name", fieldtype: "Data" }];
    return data;
  },
});

const showViewControls = computed(() => {
  return (
    !props.options.hideViewControls &&
    filterableFields.data &&
    sortableFields.data &&
    quickFilters.data
  );
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

// to handle cases where the list view is updated
defineExpose({
  reload,
});
</script>
