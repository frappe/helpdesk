<template>
  <!-- View Controls -->
  <div
    :class="[
      'flex items-center justify-between gap-2 px-5 pb-4 pt-4',
      list?.data?.data?.length > 0 || effectiveViewType === 'kanban'
        ? 'relative'
        : 'absolute inset-x-0',
    ]"
    v-if="showViewControls"
  >
    <QuickFilters v-if="!isMobileView" />
    <div v-if="!isMobileView" class="-ms-2 h-5 border-s"></div>
    <div
      class="flex items-start gap-2 justify-end h-full py-1 ps-0.5"
      v-if="!isMobileView"
    >
      <Button
        :label="__('Save Changes')"
        v-if="isViewUpdated && canSaveView"
        @click="handleViewUpdate"
      />
      <Reload @click="handleReload" :loading="list.loading" />
      <Filter />
      <SortBy :hide-label="isMobileView" />
      <ColumnSettings
        :hide-label="isMobileView"
        v-if="!options.hideColumnSetting"
      />
    </div>
    <div v-else class="flex justify-between items-center w-full">
      <Filter />
      <div class="flex items-center gap-2">
        <Reload @click="handleReload" :loading="list.loading" />
        <SortBy :hide-label="isMobileView" />
      </div>
    </div>
  </div>

  <!-- Kanban View -->
  <KanbanView
    v-if="effectiveViewType === 'kanban'"
    :doctype="options.doctype"
    :rows="list.data?.data || []"
    :loading="!!list.loading"
    :group-by-field="list.data?.group_by_field"
    :row-route="options.rowRoute"
    @card-moved="handleReload"
  />
  <!-- Loading State -->
  <div
    v-else-if="list.loading && !list.data?.data?.length"
    class="flex items-center justify-center h-full w-full absolute top-0 z-100"
  >
    <LoadingIndicator :scale="8" />
  </div>
  <!-- List View -->
  <ListView
    v-else-if="list.data?.data.length > 0"
    class="flex-1"
    :columns="columns"
    :rows="rows"
    row-key="name"
    :options="{
      selectable: options.selectable,
      showTooltip: false,
      resizeColumn: true,
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
        @columnWidthUpdated="handleColumnResize"
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
          <Button icon="lucide-more-horizontal" variant="ghost" />
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
    v-else-if="!list.loading"
    :title="emptyState.title"
    :icon="emptyState.icon"
    :description="emptyState.description"
  />
</template>

<script setup lang="ts">
import { MultipleAvatar, StarRating } from "@/components";
import {
  ColumnSettings,
  QuickFilters,
  Reload,
  SortBy,
} from "@/components/view-controls";
import { Filter, normalizeFilters } from "@/components/view-controls/filter";
import { useScreenSize } from "@/composables/screen";
import {
  currentView as headerView,
  useView,
  views,
} from "@/composables/useView";
import { useAuthStore } from "@/stores/auth";
import { globalStore } from "@/stores/globalStore";
import { useTicketStatusStore } from "@/stores/ticketStatus";
import { capture } from "@/telemetry";
import { __ } from "@/translation";
import { View, ViewType } from "@/types";
import { getIcon } from "@/utils";
import { useStorage } from "@vueuse/core";
import {
  createResource,
  Dropdown,
  frappeRequest,
  ListFooter,
  ListHeader,
  ListHeaderItem,
  ListRowItem,
  ListSelectBanner,
  ListView,
  LoadingIndicator,
  dayjs,
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
import KanbanView from "./KanbanView.vue";
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
      description?: string;
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
  (event: "rowClick", row: any): void;
}
const props = defineProps<P>();
const emit = defineEmits<E>();
const route = useRoute();
const router = useRouter();
const { isManager } = useAuthStore();
const { $dialog, $socket } = globalStore();
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
      label: __("Delete"),
      icon: "lucide-trash-2",
      onClick: (selections: Set<string>) => {
        $dialog({
          title: __("Delete"),
          message: __("Are you sure you want to delete {0} item(s)?", [
            selections.size,
          ]),
          actions: [
            {
              label: __("Delete"),
              variant: "solid",
              theme: "red",
              iconLeft: "trash-2",
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
  const requested = Array.from(selections);
  const requestedCount = requested.length;

  const failureMessages: string[] = [];
  let successMessage = "";
  let failedCount = 0;

  const onBulkResult = (data: { message: string; title: string }) => {
    const isFailure =
      data.title === __("Bulk Operation Failed") ||
      data.title === "Bulk Operation Failed";
    const isSuccess =
      data.title === __("Bulk Operation Successful") ||
      data.title === "Bulk Operation Successful";
    if (!isFailure && !isSuccess) return;

    if (isFailure) {
      // Parse how many items failed from the message (Frappe includes the count)
      const match = data.message.match(/Failed to delete (\d+) documents?/);
      if (match) {
        failedCount = parseInt(match[1], 10);
      }
      failureMessages.push(data.message);
    } else {
      successMessage = data.message;
    }
  };

  $socket.on("msgprint", onBulkResult);

  // Use frappeRequest (not `call`) so per-item delete errors surfaced in
  // `_server_messages` get routed through the app's serverMessagesHandler.
  // `call` silently drops them on 200 responses.
  frappeRequest({
    url: "frappe.desk.reportview.delete_items",
    params: {
      items: JSON.stringify(requested),
      doctype: props.options.doctype,
    },
  }).finally(() => {
    $socket.off("msgprint", onBulkResult);

    const deletedCount = requestedCount - failedCount;

    if (failureMessages.length > 0 && deletedCount > 0) {
      // Partial success: some deleted, some failed — show both toasts
      toast.success(__("{0} item(s) deleted successfully", [deletedCount]));
      for (const msg of failureMessages) {
        toast.error(msg);
      }
    } else if (failureMessages.length > 0) {
      // All failed
      for (const msg of failureMessages) {
        toast.error(msg);
      }
    } else if (successMessage) {
      // All succeeded
      toast.success(successMessage);
    } else {
      // Fallback: no socket messages received (e.g. enqueued for >10 items)
      toast.success(__("{0} item(s) queued for deletion", [requestedCount]));
    }

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
  title: __("No Data Found"),
};

const pageLengthCount = useStorage(
  `list_page_length_count+${props.options.doctype}`,
  options.value.default_page_length
);

const defaultParams = reactive({
  doctype: options.value.doctype,
  filters: {},
  default_filters: options.value.defaultFilters,
  order_by: "modified desc",
  page_length: pageLengthCount.value,
  page_length_count: pageLengthCount.value,
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

// Local override for view type (List / Group By / Kanban) — lets the user
// toggle the layout without modifying the underlying HD View record.
// Persisted per saved view (keyed by view name, or "__default__" when no
// view is selected) so the layout choice survives navigation and reloads.
type ViewType = "list" | "group_by" | "kanban";
const viewTypeMap = useStorage<Record<string, ViewType>>(
  `helpdesk:view-type:${props.options.doctype}`,
  {}
);
const currentViewKey = computed(
  () => (route.query.view as string) || "__default__"
);
const viewTypeOverride = computed<ViewType | null>({
  get: () => viewTypeMap.value[currentViewKey.value] ?? null,
  set: (val) => {
    if (val === null) {
      delete viewTypeMap.value[currentViewKey.value];
    } else {
      viewTypeMap.value[currentViewKey.value] = val;
    }
  },
});
const effectiveViewType = computed<"list" | "group_by" | "kanban">(() => {
  if (viewTypeOverride.value) return viewTypeOverride.value;
  const t = list.data?.view_type || defaultParams.view?.view_type;
  return t === "group_by" || t === "kanban" ? t : "list";
});
// `owner` is the default group_by_field on every doctype but is useless
// for kanban/group_by (one column per user). Treat it as "no preference".
function pickGroupByField(currentField: string | null, viewType: ViewType) {
  if (viewType === "list") return currentField || null;
  if (currentField && currentField !== "owner") return currentField;
  return "status";
}
// Label/icon shown in the breadcrumb when no saved view is active —
// reflects the current effective view type so "Tickets / Kanban" reads
// correctly after a layout toggle (previously stuck on "Liste").
function viewTypeBadge(t: ViewType) {
  if (t === "kanban") return { label: __("Kanban"), icon: LucideColumns3 };
  return { label: __("List"), icon: LucideAlignJustify };
}
function handleViewTypeChange(val: ViewType) {
  viewTypeOverride.value = val;
  defaultParams.view = {
    ...defaultParams.view,
    view_type: val,
    group_by_field: pickGroupByField(
      defaultParams.view?.group_by_field,
      val
    ),
  };
  // Keep the breadcrumb in sync — only when no saved view is selected.
  // For saved views, the view's label/icon remain authoritative until
  // the user explicitly saves the new type back via "Save Changes".
  if (!route.query.view) {
    const badge = viewTypeBadge(val);
    headerView.value.label = badge.label;
    headerView.value.icon = badge.icon;
  } else {
    // On a saved view: flag the change so "Save Changes" appears,
    // letting the user persist the new type into the HD View doc.
    const storedType = findView(route.query.view as string).value?.type || "list";
    if (val !== storedType) isViewUpdated.value = true;
  }
  list.submit({ ...defaultParams });
}

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
  // Lets the parent (e.g. Tickets.vue "Default Views" dropdown) switch
  // between list / kanban / group_by without rendering an inline toggle.
  setViewType: handleViewTypeChange,
  effectiveViewType,
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
  if (effectiveViewType.value === "group_by") {
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
      icon: h("span", {
        class: ["lucide-folder", "h-4 w-4 flex-shrink-0 text-ink-gray-6"],
        "aria-hidden": "true",
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
      class: "text-base",
      textContent: dayjs(item).fromNow(),
    });
  }
  if (column.type === "MultipleAvatar") {
    return h(MultipleAvatar, {
      avatars: item,
      hideName: false,
      class: "flex items-center flex-1 min-w-0",
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
    applyColumnFilter(column.key, "LIKE", `%${item}%`);
    return;
  }
  applyColumnFilter(column.key, "=", item);
}

function applyColumnFilter(key: string, operator: string, value: any) {
  const conditions = normalizeFilters(defaultParams.filters).filter(
    (condition) => condition[0] !== key
  );
  conditions.push([key, operator, value]);
  applyFilters(conditions);
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
  defaultParams.filters = normalizeFilters(filters);
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
  if (!defaultParams.is_default) return;
  handleViewUpdate();
  isViewUpdated.value = false;
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
    defaultParams.filters = normalizeFilters(options.value.defaultFilters);
    defaultParams.order_by = "modified desc";
    defaultParams.page_length = options.value.default_page_length;
    pageLengthCount.value = options.value.default_page_length;
    defaultParams.page_length_count = pageLengthCount.value;
    defaultParams.columns = [];
    defaultParams.rows = [];
    defaultParams.is_default = true;
  }
  list.reload({ ...defaultParams });
}

function handlePageLength(count: number, loadMore: boolean = false) {
  pageLengthCount.value = count;
  defaultParams.page_length_count = pageLengthCount.value;
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
  const view: Record<string, any> = {
    filters: JSON.stringify(defaultParams.filters),
    columns: JSON.stringify(defaultParams.columns),
    rows: JSON.stringify(defaultParams.rows),
    order_by: defaultParams.order_by,
    name: (route.query.view as string) || "default",
    dt: options.value.doctype,
    route_name: route.name,
    is_customer_portal: options.value.isCustomerPortal,
    // Persist the current view type + group_by_field so a saved view
    // remembers whether it should render as List or Kanban for everyone
    // (matches what the local override has been showing the user).
    type: effectiveViewType.value,
    group_by_field: defaultParams.view?.group_by_field || null,
  };
  const currentView = findView(route.query.view as string).value;
  if (currentView && currentView.public) {
    $dialog({
      title: __("Confirm Changes"),
      message: __(
        "This view is public. Changes made will be visible to everyone."
      ),
      actions: [
        {
          label: __("Save"),
          variant: "solid",
          onClick({ close }) {
            updateView(view, () => {
              isViewUpdated.value = false;
            });
            close();
          },
        },
        {
          label: __("Cancel"),
          variant: "outline",
          onClick({ close }) {
            close();
          },
        },
      ],
    });
  } else {
    updateView(view, () => {
      isViewUpdated.value = false;
    });
  }
}

const { findView, updateView, defaultView } = useView(options.value.doctype);

const canSaveView = computed(() => {
  let currentView: View = findView(route.query.view as string).value;
  if (currentView?.is_standard) return false;
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
  // normalize so legacy dict-format saved views become list conditions
  defaultParams.filters = normalizeFilters(currentView.filters);
  defaultParams.order_by = currentView.order_by || "modified desc";
  defaultParams.columns = currentView.columns;
  defaultParams.rows = currentView.rows;
  // Carry the view type + group_by_field so the backend knows how to shape
  // the response (e.g. kanban needs group_by_field expanded to {label,value}).
  // If the user has toggled to a different view type via ViewTypeSwitch,
  // keep that local override instead of resetting it from the saved view.
  const storedType = (currentView as any).type || "list";
  const effectiveType = viewTypeOverride.value || storedType;
  const storedGroupBy = (currentView as any).group_by_field;
  defaultParams.view = {
    ...defaultParams.view,
    view_type: effectiveType,
    group_by_field: pickGroupByField(
      storedGroupBy || defaultParams.view.group_by_field,
      effectiveType
    ),
    name: currentView.name,
  };

  if (route.query.filters) {
    try {
      const parsedFilters = normalizeFilters(
        JSON.parse(route.query.filters as string)
      );
      if (parsedFilters.length > 0) {
        const overriddenFields = new Set(parsedFilters.map((c) => c[0]));
        defaultParams.filters = [
          ...normalizeFilters(defaultParams.filters).filter(
            (c) => !overriddenFields.has(c[0])
          ),
          ...parsedFilters,
        ];
      }
    } catch (e) {
      console.error("Failed to parse filters from URL", e);
    }
  }

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
    // Switching to a different saved view: viewTypeOverride is keyed by
    // view name and reactively re-reads from the persisted map, so the
    // user's last layout choice for that view is restored automatically.
    handleViewChanges();
    if (!val) {
      // On the default (no saved view), the breadcrumb badge follows
      // whatever layout the user picked — kanban override included.
      const badge = viewTypeBadge(effectiveViewType.value);
      headerView.value.label = badge.label;
      headerView.value.icon = badge.icon;
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

function handleColumnResize({ key, width, save } = {}) {
  const column = columns.value.find((c) => c.key === key);
  if (column) column.width = width;
  if (!save) return;
  isViewUpdated.value = true;
  defaultParams.columns = columns.value;
  if (!defaultParams.is_default) return;
  handleViewUpdate();
  isViewUpdated.value = false;
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
      headerView.value.label = currentView.label || __("List");
      headerView.value.icon = getIcon(currentView.icon);
    }
    return;
  }
});

defineExpose(exposeFunctions);
</script>
