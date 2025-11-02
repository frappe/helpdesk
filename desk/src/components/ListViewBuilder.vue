<template>
  <!-- View Controls -->
  <div
    class="flex items-center justify-between gap-2 px-5 pb-4 pt-3 pl-6"
    v-if="showViewControls"
  >
    <QuickFilters v-if="!isMobileView" class="flex-1" />
    <div class="flex items-start gap-2 justify-end h-full" v-if="!isMobileView">
      <Button
        label="Save Changes"
        v-if="isViewUpdated && canSaveView"
        @click="handleViewUpdate"
      />
      <Reload @click="handleReload" :loading="list.loading" />
      <Filter :default_filters="defaultParams.filters" />
      <SortBy :hide-label="isMobileView" />
      <ColumnSettings
        :hide-label="isMobileView"
        v-if="!options.hideColumnSetting"
      />
    </div>
    <div v-else class="flex justify-between items-center w-full">
      <Filter :default_filters="defaultParams.filters" />
      <div class="flex items-center gap-2">
        <Reload @click="handleReload" :loading="list.loading" />
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
      selectable: options.selectable,
      showTooltip: false,
      resizeColumn: false,
      getRowRoute: (row) => ({
        name: options.rowRoute?.name,
        params: { [options.rowRoute?.prop]: row.name },
        query: { view: route.query?.view },
      }),
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
      :group-by-actions="options.groupByActions"
      @scrollend="handleListScroll"
      class="list-rows"
    >
      <ListRowItem :item="item" :column="column" :row="row">
        <component
          :is="listCell(column, row, item, idx)"
          :key="column.key"
          @click="(e) => handleFieldClick(e, column, row, item)"
        />
      </ListRowItem>
    </ListRows>
    <ListSelectBanner v-if="options.showSelectBanner">
      <template #actions="{ selections, unselectAll }">
        <Dropdown :options="selectBannerOptions(selections, unselectAll)">
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
  <!-- Loading State -->
  <div
    v-else-if="list.loading"
    class="w-full h-full flex items-center justify-center -mt-48"
  >
    <LoadingIndicator :scale="10" />
  </div>
  <!-- Empty State -->
  <EmptyState
    v-else
    :title="emptyState.title"
    :icon="emptyState.icon"
    @emptyStateAction="emit('emptyStateAction')"
  />
</template>

<script setup lang="ts">
import { MultipleAvatar, StarRating } from "@/components";
import {
  ColumnSettings,
  Filter,
  QuickFilters,
  Reload,
  SortBy,
} from "@/components/view-controls";
import { useScreenSize } from "@/composables/screen";
import {
  currentView as headerView,
  useView,
  views,
} from "@/composables/useView";
import { useAuthStore } from "@/stores/auth";
import { globalStore } from "@/stores/globalStore";
import { capture } from "@/telemetry";
import { View, ViewType } from "@/types";
import { formatTimeShort, getIcon } from "@/utils";
import { useStorage } from "@vueuse/core";

import { useTicketStatusStore } from "@/stores/ticketStatus";
import {
  call,
  createResource,
  Dropdown,
  FeatherIcon,
  ListFooter,
  ListHeader,
  ListHeaderItem,
  ListRowItem,
  ListSelectBanner,
  ListView,
  LoadingIndicator,
  toast,
} from "frappe-ui";
import {
  computed,
  h,
  onMounted,
  provide,
  reactive,
  ref,
  VNode,
  watch,
} from "vue";
import { useRoute, useRouter } from "vue-router";
import EmptyState from "./EmptyState.vue";
import ListRows from "./ListRows.vue";

interface P {
  options: {
    doctype: string;
    defaultFilters?: Record<string, any>;
    columnConfig?: Record<string, any>;
    emptyState?: {
      // type of a h componnt
      icon?: string | VNode;
      title: string;
    };
    hideViewControls?: boolean;
    hideColumnSetting?: boolean;
    selectable?: boolean;
    view?: ViewType;
    groupByActions?: Array<any>;
    showSelectBanner?: boolean;
    selectBannerActions?: Record<string, any>;
    default_page_length?: number;
    isCustomerPortal?: boolean;
    rowRoute?: Record<string, string>;
  };
}

interface E {
  (event: "emptyStateAction"): void;
  (event: "rowClick", row: any): void;
}
const props = defineProps<P>();
const emit = defineEmits<E>();
const route = useRoute();
const router = useRouter();
const { isManager } = useAuthStore();
const { $dialog } = globalStore();
const { getStatus } = useTicketStatusStore();

const listSelections = ref(new Set());
const defaultOptions = reactive({
  doctype: "",
  hideViewControls: false,
  selectable: false,
  view: {
    view_type: "list",
    group_by_field: "owner",
    name: route.query.view,
  },
  groupByActions: [],
  default_page_length: 20,
  isCustomerPortal: false,
  hideColumnSetting: true,
  rowRoute: {
    name: "",
    prop: "",
  },
  selectBannerActions: [
    {
      label: "Delete",
      icon: "trash-2",
      onClick: (selections: Set<string>) => {
        $dialog({
          title: "Delete",
          message: `Are you sure you want to delete ${selections.size} item(s)?`,
          actions: [
            {
              label: "Confirm",
              variant: "solid",
              onClick({ close }) {
                handleBulkDelete(close, selections);
              },
            },
          ],
        });
      },
      condition: () => !options.value.isCustomerPortal && isManager,
    },
  ],
});

function handleBulkDelete(hide: Function, selections: Set<string>) {
  capture("bulk_delete" + props.options.doctype);
  call("frappe.desk.reportview.delete_items", {
    items: JSON.stringify(Array.from(selections)),
    doctype: props.options.doctype,
  }).then(() => {
    toast.success("Item(s) deleted successfully");
    hide();
    reset();
  });
}

function reset() {
  exposeFunctions.reload();
  exposeFunctions.unselectAll();
}

const options = computed(() => {
  return {
    ...defaultOptions,
    ...props.options,
  };
});

const { isMobileView } = useScreenSize();

const defaultEmptyState = {
  icon: "",
  title: "No Data Found",
};

const defaultParams = reactive({
  doctype: options.value.doctype,
  filters: {},
  default_filters: options.value.defaultFilters,
  order_by: "modified desc",
  page_length: options.value.default_page_length,
  page_length_count: options.value.default_page_length,
  view: options.value.view,
  columns: [],
  rows: [],
  show_customer_portal_fields: options.value.isCustomerPortal,
  is_default: false,
});

const emptyState = computed(() => {
  return options.value?.emptyState || defaultEmptyState;
});

const isViewUpdated = ref(false);

const list = createResource({
  url: "helpdesk.api.doc.get_list_data",
  params: defaultParams,
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

const exposeFunctions = {
  list,
  reload,
  unselectAll: () => {},
};

function selectBannerOptions(selections: Set<string>, unselectAll = () => {}) {
  exposeFunctions["unselectAll"] = unselectAll;

  // Get the user-provided actions
  const userActions = options.value.selectBannerActions.map((action) => ({
    ...action,
    onClick: () => action.onClick?.(selections),
  }));

  // Get the default actions
  // overwrite the default actions if user provided actions with same label
  const defaultActions = defaultOptions.selectBannerActions
    .filter(
      (action) =>
        !userActions.some(
          (defaultAction) => defaultAction.label === action.label
        )
    )
    .map((action) => ({
      ...action,
      onClick: () => action.onClick?.(selections),
    }));

  // Return combined actions
  return [...userActions, ...defaultActions];
}

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
  if (!options.value?.columnConfig) return column;
  const columnConfig = options.value.columnConfig;
  if (!columnConfig.hasOwnProperty(column.key)) return column;
  column.prefix = columnConfig[column.key]?.prefix;

  return column;
}

const filterableFields = createResource({
  url: "helpdesk.api.doc.get_filterable_fields",
  cache: ["DocField", options.value.doctype],
  auto: !options.value.hideViewControls,
  params: {
    doctype: options.value.doctype,
    append_assign: true,
    show_customer_portal_fields: defaultParams.show_customer_portal_fields,
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
  auto: !options.value.hideViewControls,
  params: {
    doctype: options.value.doctype,
    show_customer_portal_fields: defaultParams.show_customer_portal_fields,
  },
});

const quickFilters = createResource({
  url: "helpdesk.api.doc.get_quick_filters",
  auto: !options.value.hideViewControls,
  params: {
    doctype: options.value.doctype,
    show_customer_portal_fields: defaultParams.show_customer_portal_fields,
  },
  transform: (data) => {
    if (Boolean(data.length)) return;
    data = [{ name: "name", label: "Name", fieldtype: "Data" }];
    return data;
  },
});

function listCell(column: any, row: any, item: any, idx: number) {
  const columnConfig = options.value.columnConfig;
  if (columnConfig && columnConfig[column.key]?.custom) {
    return columnConfig[column.key]?.custom({ column, row, item, idx });
  }
  if (idx === 0) {
    return h("span", {
      class: "truncate text-base text-ink-gray-6",
      textContent: item,
    });
  }
  if (column.type === "Datetime") {
    return h("span", {
      class: "text-p-xs",
      textContent: formatTimeShort(item),
    });
  }
  if (column.type === "MultipleAvatar") {
    return h(MultipleAvatar, {
      avatars: item,
      hideName: true,
      class: "flex items-center truncate flex-1 flex-row-reverse justify-end",
    });
  }
  if (column.type === "Rating") {
    return h(StarRating, {
      rating: item || 0,
      class: "truncate",
    });
  }
  return h("span", {
    class: "truncate flex-1",
    textContent: item,
  });
}

function handleFieldClick(e: MouseEvent, column, row, item) {
  const noFilterFields = ["Data", "Datetime", "Rating", "Int", "Float"];
  if (noFilterFields.includes(column.type)) {
    if (options.value.rowRoute?.name !== "") {
      return;
    }
    emit("rowClick", row.name);
    return;
  }
  e.stopPropagation();
  e.preventDefault();

  if (column.label == "Status" && options.value.doctype === "HD Ticket") {
    item = getStatus(item)?.label_agent;
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
    applyFilters({ ...defaultParams.filters, [column.key]: ["LIKE", item] });
    return;
  }
  applyFilters({ ...defaultParams.filters, [column.key]: item });
}

const showViewControls = computed(() => {
  return (
    !options.value.hideViewControls &&
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
  updateColumns,
  reload,
});

function applyFilters(filters) {
  isViewUpdated.value = true;
  defaultParams.filters = { ...filters };
  list.submit({ ...defaultParams });

  // automatically update filters for default view
  if (!defaultParams.is_default) return;
  handleViewUpdate();
  isViewUpdated.value = false;
}

function applySort(order_by: string) {
  isViewUpdated.value = true;
  defaultParams.order_by = order_by;
  list.submit({ ...defaultParams, order_by });
}

function updateColumns(obj) {
  isViewUpdated.value = true;
  const { columns: _columns, isDefault, rows } = obj;
  _columns?.forEach((column) => {
    handleFetchFromField(column);
    handleColumnConfig(column);
  });
  columns.value = defaultParams.columns = isDefault ? "" : _columns;
  defaultParams.rows = isDefault ? "" : rows;
  list.reload({ ...defaultParams });
}

function reload(reset: boolean = false) {
  if (reset) {
    defaultParams.filters = options.value.defaultFilters || {};
    defaultParams.order_by = "modified desc";
    defaultParams.page_length = options.value.default_page_length;
    defaultParams.page_length_count = options.value.default_page_length;
    defaultParams.columns = [];
    defaultParams.rows = [];
    defaultParams.is_default = true;
  }
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

function handleViewUpdate() {
  const view = {
    filters: JSON.stringify(defaultParams.filters),
    columns: JSON.stringify(defaultParams.columns),
    rows: JSON.stringify(defaultParams.rows),
    order_by: defaultParams.order_by,
    name: (route.query.view as string) || "default",
    dt: options.value.doctype,
    route_name: route.name,
    is_customer_portal: options.value.isCustomerPortal,
  };
  updateView(view, () => {
    isViewUpdated.value = false;
  });
}

const { findView, updateView, defaultView } = useView(options.value.doctype);

const canSaveView = computed(() => {
  let currentView: View = findView(route.query.view as string).value;
  if (!currentView || !currentView.public) return true;
  if (currentView.public && isManager) {
    return true;
  }
  return false;
});

function handleReload() {
  handleViewChanges();
  isViewUpdated.value = false;
}

function handleViewChanges() {
  let currentView: View = findCurrentView();
  if (!currentView) {
    router.push({ name: route.name });
    reload(true);
    return;
  }
  defaultParams.filters = currentView.filters;
  defaultParams.order_by = currentView.order_by || "modified desc";
  defaultParams.columns = currentView.columns;
  defaultParams.rows = currentView.rows;

  list.submit({ ...defaultParams });
}

function findCurrentView() {
  let currentView: View;
  if (route.query.view) {
    currentView = findView(route.query.view as string).value;
    defaultParams.is_default = false;
  } else if (defaultView.value) {
    currentView = defaultView.value;
    defaultParams.is_default = true;
  }
  return currentView;
}

watch(
  () => route.query.view,
  (val: string) => {
    defaultParams.view.name = val;
    handleViewChanges();
    if (!val) {
      headerView.value.label = "List";
      headerView.value.icon = "lucide:align-justify";
    }
  }
);

const listScrollPosition = useStorage(
  `list_position+${props.options.doctype}`,
  0
);
function handleListScroll(e) {
  listScrollPosition.value = e.target.scrollTop;
}
function handleScrollPosition() {
  setTimeout(() => {
    const listContainer = document.querySelector(".list-rows");
    if (!listContainer) return;
    listContainer.scrollTop = listScrollPosition.value;
  }, 200);
}

onMounted(async () => {
  handleScrollPosition();

  if (views.data?.length > 0 && views.filters?.dt === options.value.doctype) {
    handleViewChanges();
  } else {
    await views.list.promise;
    handleViewChanges();
  }
  if (route.query.view || defaultView.value) {
    if (route.query.view) {
      const currentView = findCurrentView();
      if (!currentView) return;
      headerView.value.label = currentView.label || "List";
      headerView.value.icon = getIcon(currentView.icon);
    }
    return;
  }
});

defineExpose(exposeFunctions);
</script>
