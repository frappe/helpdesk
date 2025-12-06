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

  <!-- List View - DaisyUI Table -->
  <div v-if="list.data?.data.length > 0" class="flex-1 overflow-hidden flex flex-col">
    <div class="overflow-x-auto overflow-y-auto flex-1 list-rows" @scroll="handleListScroll">
      <table class="table table-zebra table-pin-rows w-full">
        <!-- Table Header -->
        <thead>
          <tr class="bg-base-200">
            <!-- Checkbox column (if selectable) -->
            <th v-if="options.selectable" class="w-12">
              <label>
                <input
                  type="checkbox"
                  class="checkbox checkbox-sm"
                  :checked="allRowsSelected"
                  @change="toggleAllRows"
                />
              </label>
            </th>
            <!-- Data columns -->
            <th
              v-for="column in columnsWithActions"
              :key="column.key"
              :style="{ width: column.width || 'auto' }"
              class="font-semibold text-sm"
            >
              {{ column.label }}
            </th>
          </tr>
        </thead>
        <!-- Table Body -->
        <tbody>
          <template v-if="list.data.view_type === 'group_by'">
            <!-- Grouped rows -->
            <template v-for="group in rows" :key="group.group.value">
              <!-- Group header row -->
              <tr class="bg-base-300 hover:bg-base-300">
                <td
                  :colspan="columnsWithActions.length + (options.selectable ? 1 : 0)"
                  class="font-semibold cursor-pointer"
                  @click="group.collapsed = !group.collapsed"
                >
                  <div class="flex items-center gap-2">
                    <FeatherIcon
                      :name="group.collapsed ? 'chevron-right' : 'chevron-down'"
                      class="h-4 w-4"
                    />
                    <component :is="group.icon" />
                    <span>{{ group.group.label || 'No Value' }}</span>
                    <span class="badge badge-sm">{{ group.rows.length }}</span>
                  </div>
                </td>
              </tr>
              <!-- Group rows -->
              <tr
                v-for="(row, rowIdx) in group.rows"
                v-show="!group.collapsed"
                :key="row.name"
                class="hover:bg-base-200 cursor-pointer transition-colors"
              >
                <!-- Checkbox cell -->
                <td v-if="options.selectable" class="w-12">
                  <label>
                    <input
                      type="checkbox"
                      class="checkbox checkbox-sm"
                      :checked="isRowSelected(row.name)"
                      @change="() => toggleRow(row.name)"
                    />
                  </label>
                </td>
                <!-- Data cells -->
                <td
                  v-for="(column, colIdx) in columnsWithActions"
                  :key="column.key"
                  :style="{ width: column.width || 'auto' }"
                  class="py-2"
                >
                  <component
                    :is="renderCell(column, row, row[column.key], rowIdx)"
                  />
                </td>
              </tr>
            </template>
          </template>
          <template v-else>
            <!-- Regular rows -->
            <tr
              v-for="(row, rowIdx) in rows"
              :key="row.name"
              class="hover:bg-base-200 cursor-pointer transition-colors"
            >
              <!-- Checkbox cell -->
              <td v-if="options.selectable" class="w-12">
                <label>
                  <input
                    type="checkbox"
                    class="checkbox checkbox-sm"
                    :checked="isRowSelected(row.name)"
                    @change="() => toggleRow(row.name)"
                  />
                </label>
              </td>
              <!-- Data cells -->
              <td
                v-for="(column, colIdx) in columnsWithActions"
                :key="column.key"
                :style="{ width: column.width || 'auto' }"
                class="py-2"
              >
                <component
                  :is="renderCell(column, row, row[column.key], rowIdx)"
                />
              </td>
            </tr>
          </template>
        </tbody>
      </table>
    </div>
    <!-- Select Banner -->
    <div
      v-if="options.showSelectBanner && selectedRows.size > 0"
      class="bg-primary text-primary-content p-3 flex items-center justify-between"
    >
      <div class="flex items-center gap-3">
        <span class="font-medium">{{ selectedRows.size }} selected</span>
        <button class="btn btn-ghost btn-sm" @click="unselectAll">Clear</button>
      </div>
      <div class="flex items-center gap-2">
        <Dropdown :options="selectBannerOptions(selectedRows, unselectAll)">
          <Button icon="more-horizontal" variant="ghost" />
        </Dropdown>
      </div>
    </div>
  </div>

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
import { ListFooter } from "frappe-ui";
import {
  Button,
  LoadingIndicator,
  Dropdown,
  call,
  createResource,
  FeatherIcon,
  toast,
} from "@/components/ui";
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

// Inline editor components
import StatusInlineEdit from "./inline-editors/StatusInlineEdit.vue";
import PriorityInlineEdit from "./inline-editors/PriorityInlineEdit.vue";
import TeamInlineEdit from "./inline-editors/TeamInlineEdit.vue";
import AssigneeInlineEdit from "./inline-editors/AssigneeInlineEdit.vue";
import SubjectInlineEdit from "./inline-editors/SubjectInlineEdit.vue";
import TicketTypeInlineEdit from "./inline-editors/TicketTypeInlineEdit.vue";

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
const selectedRows = ref(new Set());

// Row selection functions
function toggleRow(rowName: string) {
  if (selectedRows.value.has(rowName)) {
    selectedRows.value.delete(rowName);
  } else {
    selectedRows.value.add(rowName);
  }
  selectedRows.value = new Set(selectedRows.value); // Trigger reactivity
}

function toggleAllRows() {
  if (allRowsSelected.value) {
    selectedRows.value.clear();
  } else {
    rows.value.forEach((row) => {
      if (row.rows) {
        // Grouped rows
        row.rows.forEach((r) => selectedRows.value.add(r.name));
      } else {
        selectedRows.value.add(row.name);
      }
    });
  }
  selectedRows.value = new Set(selectedRows.value); // Trigger reactivity
}

function unselectAll() {
  selectedRows.value.clear();
  selectedRows.value = new Set(selectedRows.value); // Trigger reactivity
}

function isRowSelected(rowName: string) {
  return selectedRows.value.has(rowName);
}

const allRowsSelected = computed(() => {
  if (rows.value.length === 0) return false;

  let totalRows = 0;
  rows.value.forEach((row) => {
    if (row.rows) {
      totalRows += row.rows.length;
    } else {
      totalRows += 1;
    }
  });

  return selectedRows.value.size === totalRows && totalRows > 0;
});

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

// Add actions column at the end (far right)
const columnsWithActions = computed(() => {
  if (!columns.value || columns.value.length === 0) return [];

  return [
    ...columns.value,
    {
      label: '',
      key: '_actions',
      width: '200px', // Width for 5 action buttons
    },
  ];
});

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

function renderCell(column: any, row: any, item: any, idx: number) {
  // Handle actions column - Gmail-style email actions with DaisyUI buttons
  if (column.key === '_actions') {
    return h('div', {
      class: 'flex items-center gap-1',
    }, [
      // Reply-All button
      h('button', {
        class: 'btn btn-ghost btn-xs btn-square',
        title: 'Reply all',
        onClick: (e) => {
          e.stopPropagation();
          router.push({
            name: options.value.rowRoute?.name,
            params: { [options.value.rowRoute?.prop]: row.name },
            query: { view: route.query?.view, action: 'reply-all' },
          });
        },
      }, [
        h(FeatherIcon, {
          name: 'corner-up-left',
          class: 'h-4 w-4 text-info',
        })
      ]),

      // Reply Sender Only button
      h('button', {
        class: 'btn btn-ghost btn-xs btn-square',
        title: 'Reply to sender',
        onClick: (e) => {
          e.stopPropagation();
          router.push({
            name: options.value.rowRoute?.name,
            params: { [options.value.rowRoute?.prop]: row.name },
            query: { view: route.query?.view, action: 'reply' },
          });
        },
      }, [
        h(FeatherIcon, {
          name: 'reply',
          class: 'h-4 w-4 text-info',
        })
      ]),

      // Forward button
      h('button', {
        class: 'btn btn-ghost btn-xs btn-square',
        title: 'Forward',
        onClick: (e) => {
          e.stopPropagation();
          router.push({
            name: options.value.rowRoute?.name,
            params: { [options.value.rowRoute?.prop]: row.name },
            query: { view: route.query?.view, action: 'forward' },
          });
        },
      }, [
        h(FeatherIcon, {
          name: 'corner-up-right',
          class: 'h-4 w-4 text-secondary',
        })
      ]),

      // Mark Closed button
      h('button', {
        class: 'btn btn-ghost btn-xs btn-square',
        title: 'Mark as closed',
        onClick: async (e) => {
          e.stopPropagation();
          try {
            await call('frappe.client.set_value', {
              doctype: 'HD Ticket',
              name: row.name,
              fieldname: 'status',
              value: 'Closed',
            });
            toast.success('Ticket marked as closed');
            list.reload();
          } catch (error) {
            console.error('[ListViewBuilder] Close ticket error:', error);
            toast.error('Failed to close ticket');
          }
        },
      }, [
        h(FeatherIcon, {
          name: 'check-circle',
          class: 'h-4 w-4 text-success',
        })
      ]),

      // Delete button
      h('button', {
        class: 'btn btn-ghost btn-xs btn-square',
        title: 'Delete ticket',
        onClick: (e) => {
          e.stopPropagation();
          $dialog({
            title: 'Delete Ticket',
            message: `Are you sure you want to delete ticket ${row.name}?`,
            actions: [
              {
                label: 'Cancel',
                variant: 'ghost',
              },
              {
                label: 'Delete',
                variant: 'solid',
                theme: 'red',
                async onClick({ close }) {
                  try {
                    await call('frappe.client.delete', {
                      doctype: 'HD Ticket',
                      name: row.name,
                    });
                    toast.success('Ticket deleted successfully');
                    close();
                    list.reload();
                  } catch (error) {
                    console.error('[ListViewBuilder] Delete error:', error);
                    toast.error('Failed to delete ticket');
                  }
                },
              },
            ],
          });
        },
      }, [
        h(FeatherIcon, {
          name: 'trash-2',
          class: 'h-4 w-4 text-error',
        })
      ]),
    ]);
  }

  const columnConfig = options.value.columnConfig;
  if (columnConfig && columnConfig[column.key]?.custom) {
    return columnConfig[column.key]?.custom({ column, row, item, idx });
  }

  // Special handling for subject column - clickable to open ticket (Gmail-style)
  if (column.key === 'subject') {
    return h('button', {
      class: 'btn btn-ghost btn-sm justify-start text-left font-semibold hover:underline normal-case p-0 min-h-0 h-auto',
      onClick: (e) => {
        e.stopPropagation();
        router.push({
          name: options.value.rowRoute?.name,
          params: { [options.value.rowRoute?.prop]: row.name },
          query: { view: route.query?.view },
        });
      },
    }, item || 'No Subject');
  }

  // Inline editor components mapping (subject removed - it's now clickable)
  const inlineEditorsMap = {
    'status': StatusInlineEdit,
    'priority': PriorityInlineEdit,
    'agent_group': TeamInlineEdit,
    '_assign': AssigneeInlineEdit,
    'ticket_type': TicketTypeInlineEdit,
  };

  // Debug: log column keys to see what's available
  if (idx === 0 && column.key !== '_actions') {
    console.log('[ListViewBuilder] Column key:', column.key, 'Item:', item);
  }

  // Check if this column should use inline editor
  if (inlineEditorsMap[column.key]) {
    const InlineEditor = inlineEditorsMap[column.key];
    return h(InlineEditor, {
      modelValue: item,
      ticketId: row.name,
      editable: true,
      'onUpdate:modelValue': (newValue) => {
        // Update will be handled by the editor's 'updated' event
      },
      onUpdated: async ({ field, value, action }) => {
        console.log(`[ListViewBuilder] Updating ${field} to ${value} for ticket ${row.name}`);
        try {
          // Handle assignment specially using Frappe's assignment API
          if (field === '_assign' && action === 'assign') {
            // First, get current assignments and remove them
            const currentAssignees = row._assign ? JSON.parse(row._assign) : [];

            // Remove all current assignees
            for (const assignee of currentAssignees) {
              await call('frappe.desk.form.assign_to.remove', {
                doctype: 'HD Ticket',
                name: row.name,
                assign_to: assignee,
              });
            }

            // Add new assignee if value is not null
            if (value) {
              await call('frappe.desk.form.assign_to.add', {
                doctype: 'HD Ticket',
                name: row.name,
                assign_to: value,
                description: 'Assigned via inline edit',
              });
            }

            toast.success('Ticket assigned successfully');
          } else {
            // Use standard set_value for other fields
            await call('frappe.client.set_value', {
              doctype: 'HD Ticket',
              name: row.name,
              fieldname: field,
              value: value,
            });
            toast.success('Ticket updated successfully');
          }

          // Reload the list to show updated value
          list.reload();
        } catch (error) {
          console.error('[ListViewBuilder] Update error:', error);
          toast.error('Failed to update ticket');
        }
      },
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
