<template>
  <!-- View Controls -->
  <div
    class="flex items-center justify-between gap-2 px-5 pb-4 pt-3"
    v-if="showViewControls"
  >
    <QuickFilters v-if="!isMobileView" />
    <div class="flex items-center gap-2" v-if="!isMobileView">
      <Reload @click="reload" :loading="list.loading" />
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
  </div>

  <!-- List View -->
  <ListView
    v-if="list.data?.data.length > 0"
    class="flex-1"
    :columns="columns"
    :rows="rows"
    row-key="name"
    :options="{
      selectable: props.options.selectable ?? true,
      showTooltip: false,
      resizeColumn: false,
      onRowClick: () => {},
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
    <ListRows
      :rows="rows"
      v-slot="{ idx, column, item, row }"
      :group-by-actions="props.options.groupByActions"
    >
      <ListRowItem :item="item" :column="column" :row="row">
        <component
          :is="listCell(column, row, item, idx)"
          :key="column.key"
          @click="(e) => handleFieldClick(e, column, row, item)"
        />
      </ListRowItem>
    </ListRows>
    <ListSelectBanner v-if="props.options.showSelectBanner">
      <template #actions="{ selections }">
        <Dropdown :options="selectBannerOptions(selections)">
          <Button icon="more-horizontal" variant="ghost" />
        </Dropdown>
      </template>
    </ListSelectBanner>
  </ListView>

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
import { reactive, provide, computed, h, ref } from "vue";
import {
  createResource,
  ListView,
  ListFooter,
  ListRowItem,
  ListHeader,
  ListHeaderItem,
  ListSelectBanner,
  FeatherIcon,
  Dropdown,
} from "frappe-ui";

import {
  Filter,
  SortBy,
  QuickFilters,
  Reload,
} from "@/components/view-controls";
import { MultipleAvatar, StarRating } from "@/components";
import { dayjs } from "@/dayjs";
import ListRows from "./ListRows.vue";
import { useScreenSize } from "@/composables/screen";
import EmptyState from "./EmptyState.vue";
import { View } from "@/types";

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
    view?: View;
    groupByActions?: Array<any>;
    showSelectBanner?: boolean;
    selectBannerActions?: Record<string, any>;
    default_page_length?: number;
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
      view: {
        view_type: "list",
        group_by_field: "owner",
      },
      groupByActions: [],
      default_page_length: 20,
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
  page_length: props.options.default_page_length,
  page_length_count: props.options.default_page_length,
  view: props.options.view,
});

const emptyState = computed(() => {
  return props.options?.emptyState || defaultEmptyState;
});

function selectBannerOptions(selections: Set<string>) {
  return props.options.selectBannerActions.map((action) => {
    return {
      ...action,
      onClick: () => action.onClick(selections),
    };
  });
}

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
  onSuccess: (data) => {
    list.params = defaultParams;
    columns.value = data.columns;
  },
});

const rows = computed(() => {
  if (!list.data?.data) return [];
  if (list.data.view_type === "group_by") {
    if (!list.data?.group_by_field?.name) return [];
    return getGroupedByRows(list.data.data, list.data.group_by_field);
  }
  return list.data?.data;
});
const columns = ref([]);

function getGroupedByRows(listRows, groupByField) {
  let groupedRows = [];
  groupByField.options?.forEach((option) => {
    let filteredRows = [];

    if (!option.value) {
      filteredRows = listRows.filter((row) => !row[groupByField.name]);
    } else {
      filteredRows = listRows.filter(
        (row) => row[groupByField.name] == option.value
      );
    }

    let groupDetail = {
      group: option || " ",
      collapsed: false,
      rows: filteredRows,
      icon: h(FeatherIcon, {
        name: "folder",
        class: "h-4 w-4 flex-shrink-0 text-ink-gray-6",
      }),
    };
    groupedRows.push(groupDetail);
  });
  return groupedRows || listRows;
}

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

function listCell(column: any, row: any, item: any, idx: number) {
  const columnConfig = props.options.columnConfig;
  if (columnConfig && columnConfig[column.key]?.custom) {
    return columnConfig[column.key]?.custom({ column, row, item, idx });
  }
  if (idx === 0) {
    return h("span", {
      class: "truncate text-base text-ink-gray-6",
      innerHTML: item,
    });
  }
  if (column.type === "Datetime") {
    return h("span", {
      class: "text-base",
      innerHTML: dayjs.tz(item).fromNow(),
    });
  }
  if (column.type === "MultipleAvatar") {
    return h(MultipleAvatar, {
      avatars: item,
      class: "flex items-center",
    });
  }
  if (column.type === "Rating") {
    return h(StarRating, {
      rating: item || 0,
      class: "truncate",
    });
  }
  return h("span", {
    class: "truncate",
    innerHTML: item,
  });
}

function handleFieldClick(e: MouseEvent, column, row, item) {
  const noFilterFields = ["Data", "Datetime", "Rating", "Int", "Float"];
  if (noFilterFields.includes(column.type)) {
    emit("rowClick", row.name);
    return;
  }
  if (column.type === "MultipleAvatar") {
    if (item.length > 1) {
      let target = e.target as HTMLElement;
      target = target.closest(".user-avatar");
      if (target) {
        item = target.getAttribute("data-name");
      }
    } else {
      item = item[0].name;
    }
    applyFilters({ ...defaultParams.filters, [column.key]: item });
    return;
  }
  applyFilters({ ...defaultParams.filters, [column.key]: item });
}

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
  list.submit({ ...defaultParams });
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
