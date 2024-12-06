<template>
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
  <slot v-bind="{ list }">
    <ListView
      class="flex-1"
      :columns="list.data?.columns"
      :rows="list.data?.data"
      row-key="email"
      :options="{
        selectable: true,
        showTooltip: true,
        resizeColumn: false,
        onRowClick: () => {},
        emptyState: props.options?.emptyState || defaultEmptyState,
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
            <div v-if="idx === 0">
              {{ item }}
            </div>
            <div
              v-else-if="column.type === 'Datetime'"
              @click="console.log('Datetime clicked')"
            >
              {{ dayjs.tz(item).fromNow() }}
            </div>
            <div v-else>
              {{ item }}
            </div>
          </ListRowItem>
        </ListRow>
      </ListRows>
    </ListView>
  </slot>

  <!-- List Footer -->
  <div class="p-20 border-t sm:px-5 px-3 py-2">
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
} from "frappe-ui";
import { Filter, SortBy, QuickFilters } from "@/components/view-controls";
import { dayjs } from "@/dayjs";
interface P {
  options: {
    doctype: string;
    default_filters?: Record<string, any>;
    column_config?: Record<string, any>;
    emptyState?: {
      title: string;
      description?: string;
      button?: {
        label: string;
        variant: string;
        onClick: () => void;
      };
    };
  };
}

interface E {
  (event: "emptyStateAction"): void;
}

const props = defineProps<P>();

const emit = defineEmits<E>();

const defaultEmptyState = {
  title: "No Data",
  description: "No data available",
};

const defaultParams = reactive({
  doctype: props.options.doctype,
  filters: props.options.default_filters || {},
  order_by: "",
  page_length: 20,
  page_length_count: 20,
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

const rows = computed(() => [] || list.data?.data);
const columns = computed(() => list.data?.columns);

function handleFetchFromField(column) {
  if (!column.hasOwnProperty("key")) return column;
  const regex = /([a-zA-Z0-9_]+)\.([a-zA-Z0-9_]+)/;
  const isFetchFromField = column.key.match(regex);
  column.key = isFetchFromField ? isFetchFromField[2] : column.key;
}

function handleColumnConfig(column) {
  if (!props.options?.column_config) return column;
  const columnConfig = props.options.column_config;
  if (!columnConfig.hasOwnProperty(column.key)) return column;
  column.prefix = columnConfig[column.key]?.prefix;

  return column;
}

const filterableFields = createResource({
  url: "helpdesk.api.doc.get_filterable_fields",
  cache: ["DocField", props.options.doctype],
  auto: true,
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
  auto: true,
  params: {
    doctype: props.options.doctype,
  },
});

const quickFilters = createResource({
  url: "helpdesk.api.doc.get_quick_filters",
  auto: true,
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
