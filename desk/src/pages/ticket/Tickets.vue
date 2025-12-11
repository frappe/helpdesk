<template>
  <div>
    <LayoutHeader>
      <template #left-header>
        <ViewBreadcrumbs
          label="Tickets"
          :route-name="isCustomerPortal ? 'TicketsCustomer' : 'TicketsAgent'"
          :options="dropdownOptions"
          :dropdown-actions="viewActions"
          :current-view="currentView"
        />
      </template>
      <template #right-header>
      <div class="flex items-center gap-2">
        <div
          class="flex items-center gap-1 rounded-lg border border-outline-gray-2 bg-surface-white p-1"
        >
          <Button
            variant="ghost"
            theme="gray"
            class="h-9 w-9"
            :class="
              isTableView
                ? 'bg-surface-gray-2 border border-outline-gray-3'
                : ''
            "
            :aria-pressed="isTableView"
            @click="viewMode = 'table'"
          >
            <LucideLayoutList class="h-4 w-4" />
          </Button>
          <Button
            variant="ghost"
            theme="gray"
            class="h-9 w-9"
            :class="
              !isTableView
                ? 'bg-surface-gray-2 border border-outline-gray-3'
                : ''
            "
            :aria-pressed="!isTableView"
            @click="viewMode = 'card'"
          >
            <LucideLayoutGrid class="h-4 w-4" />
          </Button>
        </div>
        <RouterLink
          :to="{ name: isCustomerPortal ? 'TicketNew' : 'TicketAgentNew' }"
        >
          <Button label="Create" theme="gray" variant="solid">
            <template #prefix>
              <LucidePlus class="h-4 w-4" />
            </template>
          </Button>
        </RouterLink>
      </div>
      </template>
    </LayoutHeader>
  <div v-show="isTableView">
    <ListViewBuilder
      ref="listViewRef"
      :options="options"
      @empty-state-action="
        () =>
          $router.push({
            name: isCustomerPortal ? 'TicketNew' : 'TicketAgentNew',
          })
      "
      @row-click="
        (row) =>
          $router.push({
            name: isCustomerPortal ? 'TicketCustomer' : 'TicketAgent',
            params: { ticketId: row },
          })
      "
    />
  </div>
  <div v-if="!isTableView" class="flex gap-4 px-5 pb-6 pt-3">
    <div class="flex-1">
      <TicketCardView
        :rows="cardRows"
        :loading="listLoading"
        :status-options="statusOptionList"
        :priority-options="priorityOptionList"
        @row-click="handleCardClick"
        @update-status="(ticketId, value) => handleCardStatus(ticketId, value)"
        @update-priority="(ticketId, value) => handleCardPriority(ticketId, value)"
      />
      <div v-if="ticketRows.length > 0" class="mt-2">
        <Button
          variant="outline"
          theme="gray"
          class="w-full sm:w-auto"
          :loading="listLoading"
          @click="handleCardLoadMore"
        >
          Load more
        </Button>
      </div>
    </div>
    <div
      class="hidden lg:flex w-80 shrink-0 flex-col gap-5 rounded-lg border border-outline-gray-2 bg-surface-white p-5 shadow-sm h-fit sticky top-4"
    >
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-2 text-lg font-semibold text-ink-gray-9">
          <LucideFilter class="h-5 w-5" />
          <span>Filters</span>
        </div>
        <Button size="sm" variant="ghost" theme="gray" @click="resetCardFilters">
          Reset
        </Button>
      </div>
      <div class="space-y-5 border-t border-outline-gray-2 pt-5">
        <div class="space-y-2">
          <label class="block text-xs font-semibold text-ink-gray-7 uppercase tracking-wide">
            Status
          </label>
          <MultiSelectCombobox
            v-model="cardFilters.status"
            :options="statusFilterOptions"
            placeholder="All Status"
            @update:modelValue="applyCardFilters"
            :multiple="true"
            :button-classes="'!h-9 !bg-surface-white border border-outline-gray-2 hover:!bg-surface-gray-1'"
          >
            <template #item-prefix="{ option, selected }">
              <span
                v-if="option.value"
                class="h-2 w-2 rounded-full mr-2"
                :class="option.indicatorClass"
              />
            </template>
          </MultiSelectCombobox>
        </div>
        
        <div class="space-y-2">
          <label class="block text-xs font-semibold text-ink-gray-7 uppercase tracking-wide">
            Priority
          </label>
          <MultiSelectCombobox
            v-model="cardFilters.priority"
            :options="priorityFilterOptions"
            placeholder="Any Priority"
            @update:modelValue="applyCardFilters"
            :multiple="true"
            :button-classes="'!h-9 !bg-surface-white border border-outline-gray-2 hover:!bg-surface-gray-1'"
          />
        </div>
        
        <div class="space-y-2">
          <label class="block text-xs font-semibold text-ink-gray-7 uppercase tracking-wide">
            Department
          </label>
          <MultiSelectCombobox
            v-model="cardFilters.department"
            :options="departmentFilterOptions"
            placeholder="Any Department"
            @update:modelValue="applyCardFilters"
            :multiple="true"
            :button-classes="'!h-9 !bg-surface-white border border-outline-gray-2 hover:!bg-surface-gray-1'"
          />
        </div>
        
        <div class="space-y-2">
          <label class="block text-xs font-semibold text-ink-gray-7 uppercase tracking-wide">
            Agent
          </label>
          <MultiSelectCombobox
            v-model="cardFilters.agent"
            :options="agentFilterOptions"
            placeholder="Any Agent"
            @update:modelValue="applyCardFilters"
            :multiple="true"
            :button-classes="'!h-9 !bg-surface-white border border-outline-gray-2 hover:!bg-surface-gray-1'"
          />
        </div>
      </div>
      
      <!-- Quick Views Section -->
      <div class="space-y-3 border-t border-outline-gray-2 pt-5">
        <div class="text-xs font-semibold text-ink-gray-7 uppercase tracking-wide">
          Quick Views
        </div>
        <div class="space-y-1">
          <button
            v-for="view in quickViews"
            :key="view.label"
            class="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-sm text-ink-gray-8 transition-colors hover:bg-surface-gray-1 hover:text-ink-gray-9"
            :class="{ 'bg-surface-gray-2 font-medium text-ink-gray-9': activeQuickView === view.label }"
            @click="applyQuickView(view)"
          >
            <component :is="view.icon" class="h-4 w-4 flex-shrink-0" />
            <span class="truncate">{{ view.label }}</span>
          </button>
        </div>
      </div>
    </div>
  </div>
    <ExportModal
      v-model="showExportModal"
      :rowCount="$refs.listViewRef?.list?.data?.total_count ?? 0"
      @update="
        ({ export_type, export_all }) => exportRows(export_type, export_all)
      "
    />
    <ViewModal
      v-if="viewDialog.show"
      v-model="viewDialog"
      @update="(view, action) => handleView(view, action)"
    />
  </div>
</template>

<script setup lang="ts">
import { LayoutHeader, ListViewBuilder } from "@/components";
import {
  EditIcon,
  IndicatorIcon,
  PinIcon,
  TicketIcon,
  UnpinIcon,
} from "@/components/icons";
import ExportModal from "@/components/ticket/ExportModal.vue";
import TicketRowActions from "@/components/ticket/TicketRowActions.vue";
import ViewBreadcrumbs from "@/components/ViewBreadcrumbs.vue";
import ViewModal from "@/components/ViewModal.vue";
import { currentView, useView } from "@/composables/useView";
import { dayjs } from "@/dayjs";
import TicketCardView from "@/components/ticket/TicketCardView.vue";
import MultiSelectCombobox from "@/components/frappe-ui/MultiSelectCombobox.vue";
import { useAuthStore } from "@/stores/auth";
import { globalStore } from "@/stores/globalStore";
import { useTicketStatusStore } from "@/stores/ticketStatus";
import { View } from "@/types";
import { getIcon, isCustomerPortal } from "@/utils";
import { Badge, FeatherIcon, toast, Tooltip, usePageMeta, Dropdown, call, createResource } from "frappe-ui";
import { computed, h, onMounted, onUnmounted, reactive, ref, watch } from "vue";
import { useStorage } from "@vueuse/core";
import { useRoute, useRouter } from "vue-router";
import LucidePencil from "~icons/lucide/pencil";
import LucideLayoutList from "~icons/lucide/layout-list";
import LucideLayoutGrid from "~icons/lucide/layout-grid";
import LucideFilter from "~icons/lucide/filter";
import LucideAlignJustify from "~icons/lucide/align-justify";
import LucidePlus from "~icons/lucide/plus";
import LucideInbox from "~icons/lucide/inbox";
import LucideMailOpen from "~icons/lucide/mail-open";
import LucideAlertCircle from "~icons/lucide/alert-circle";
import LucideEye from "~icons/lucide/eye";
import LucideUser from "~icons/lucide/user";
import LucideAtSign from "~icons/lucide/at-sign";
import LucideShare2 from "~icons/lucide/share-2";
import LucideUsers from "~icons/lucide/users";

const router = useRouter();
const route = useRoute();

const {
  getCurrentUserViews,
  createView,
  publicViews,
  pinnedViews,
  findView,
  updateView,
  deleteView,
} = useView("HD Ticket");

const { $dialog, $socket } = globalStore();
const { isManager } = useAuthStore();

const listViewRef = ref<any>(null);
const viewMode = useStorage<"table" | "card">("tickets_view_mode", "table");
const isTableView = computed(() => viewMode.value === "table");
const ticketRows = computed(() => listViewRef.value?.list?.data?.data || []);
const cardRows = computed(() => {
  const rows = ticketRows.value || [];
  return [...rows].sort((a, b) => statusRank(a) - statusRank(b));
});
const listLoading = computed(() => listViewRef.value?.list?.loading);
const cardFilters = reactive({
  status: [] as string[],
  priority: [] as string[],
  department: [] as string[],
  agent: [] as string[],
});
const activeQuickView = ref<string>("");
const showExportModal = ref(false);
const currentUserEmail = computed(() => useAuthStore().userResource?.email || "");

const quickViews = computed(() => [
  {
    label: "All tickets",
    icon: LucideInbox,
    filters: {},
  },
  {
    label: "All unresolved tickets",
    icon: LucideAlertCircle,
    filters: {
      status: ["!=", "Resolved"],
    },
  },
  {
    label: "New and my open tickets",
    icon: LucideMailOpen,
    filters: {
      status: ["in", ["Open", "New"]],
      assigned_to: currentUserEmail.value,
    },
  },
  {
    label: "Tickets I raised",
    icon: LucideUser,
    filters: {
      raised_by: currentUserEmail.value,
    },
  },
  {
    label: "Tickets I'm watching",
    icon: LucideEye,
    filters: {
      _liked_by: ["like", `%${currentUserEmail.value}%`],
    },
  },
  {
    label: "Tickets I've shared",
    icon: LucideShare2,
    filters: {
      _shared_by: currentUserEmail.value,
    },
  },
]);

const { getStatus, statuses } = useTicketStatusStore();

// Priority options
const priorities = createResource({
  url: "frappe.client.get_list",
  params: {
    doctype: "HD Ticket Priority",
    fields: ["name"],
    orderBy: "`tabHD Ticket Priority`.order",
    limit: 100,
  },
  auto: true,
});

const listSelections = ref(new Set());
const selectBannerActions = [
  {
    label: "Export",
    icon: "download",
    onClick: (selections: Set<string>) => {
      listSelections.value = new Set(selections);
      showExportModal.value = true;
    },
  },
];

// Update ticket field function
async function updateTicketField(ticketId: string, field: string, value: string) {
  try {
    await call("frappe.client.set_value", {
      doctype: "HD Ticket",
      name: ticketId,
      fieldname: field,
      value: value,
    });
    toast.success("Updated successfully");
    // Reload the list to reflect changes
    await listViewRef.value?.reload(false);
  } catch (error: any) {
    toast.error(error.message || "Failed to update");
  }
}

const options = {
  doctype: "HD Ticket",
  columnConfig: {
    status: {
      custom: ({ item, row }) => {
        const status = getStatus(item);
        const label = isCustomerPortal.value
          ? status?.["label_customer"]
          : status?.["label_agent"];
        
        const statusOptions = (statuses.data || []).map((s) => ({
          label: s.label_agent,
          icon: () => h(IndicatorIcon, { class: s.parsed_color }),
          onClick: () => updateTicketField(row.name, "status", s.label_agent),
        }));
        
        return h("div", { class: "group relative" }, [
          h(
            Dropdown,
            {
              options: statusOptions,
              placement: "right",
            },
            {
              default: () =>
                h(
                  "div",
                  { class: "flex items-center space-x-2 justify-start w-full px-2 py-1 rounded hover:bg-surface-gray-2 cursor-pointer" },
                  [
                    h(IndicatorIcon, { class: status?.["parsed_color"] }),
                    h("span", { class: "truncate flex-1" }, label),
                    h(LucidePencil, { class: "size-3 text-ink-gray-5 opacity-0 group-hover:opacity-100 transition-opacity" }),
                  ]
                ),
            }
          ),
        ]);
      },
    },
    priority: {
      custom: ({ item, row }) => {
        const priorityOptions = (priorities.data || []).map((p) => ({
          label: p.name,
          onClick: () => updateTicketField(row.name, "priority", p.name),
        }));
        
        return h("div", { class: "group relative" }, [
          h(
            Dropdown,
            {
              options: priorityOptions,
              placement: "right",
            },
            {
              default: () =>
                h(
                  "div",
                  { class: "flex items-center space-x-2 justify-start w-full px-2 py-1 rounded hover:bg-surface-gray-2 cursor-pointer" },
                  [
                    h("span", { class: "truncate flex-1" }, item || "None"),
                    h(LucidePencil, { class: "size-3 text-ink-gray-5 opacity-0 group-hover:opacity-100 transition-opacity" }),
                  ]
                ),
            }
          ),
        ]);
      },
    },
    agreement_status: {
      custom: ({ item }) => {
        return h(Badge, {
          label: item,
          theme: slaStatusColorMap[item],
          variant: "outline",
        });
      },
    },
    response_by: {
      custom: ({ row, item }) => handle_response_by_field(row, item),
    },
    resolution_by: {
      custom: ({ row, item }) => handle_resolution_by_field(row, item),
    },
    actions: {
      custom: ({ row }) => {
        if (isCustomerPortal.value) return null;
        return h(TicketRowActions, {
          ticket: row,
          onUpdate: () => listViewRef.value?.reload(false),
        });
      },
    },
  },
  isCustomerPortal: isCustomerPortal.value,
  selectable: true,
  showSelectBanner: true,
  selectBannerActions,
  emptyState: {
    title: "No Tickets Found",
    icon: h(TicketIcon, {
      class: "h-10 w-10",
    }),
  },
  rowRoute: {
    name: isCustomerPortal.value ? "TicketCustomer" : "TicketAgent",
    prop: "ticketId",
  },
  hideColumnSetting: false,
};

const statusOptionList = computed(() =>
  (statuses.data || []).map((s) => ({
    label: isCustomerPortal.value ? s.label_customer : s.label_agent,
    value: s.label_agent,
    indicatorClass: s.parsed_color,
    category: s.category,
  }))
);

const priorityOptionList = computed(() =>
  (priorities.data || []).map((p) => p.name)
);

const departmentOptions = createResource({
  url: "frappe.client.get_list",
  params: {
    doctype: "Department",
    fields: ["name", "department_name"],
    limit: 100,
  },
  auto: true,
});

const agentOptions = createResource({
  url: "frappe.client.get_list",
  params: {
    doctype: "HD Agent",
    fields: ["name", "agent_name"],
    limit: 100,
  },
  auto: true,
});

// Filter dropdown options
const statusFilterOptions = computed(() => {
  const options = (statuses.data || []).map((s) => ({
    label: isCustomerPortal.value ? s.label_customer : s.label_agent,
    value: s.label_agent,
    indicatorClass: s.parsed_color,
    category: s.category,
  }));
  return options;
});

const priorityFilterOptions = computed(() =>
  (priorities.data || []).map((p) => ({
    label: p.name,
    value: p.name,
  }))
);

const departmentFilterOptions = computed(() =>
  (departmentOptions.data || []).map((d) => ({
    label: d.department_name || d.name,
    value: d.name,
  }))
);

const agentFilterOptions = computed(() =>
  (agentOptions.data || []).map((a) => ({
    label: a.agent_name || a.name,
    value: a.name,
  }))
);

function handle_response_by_field(row: any, item: string) {
  if (!row.first_responded_on && dayjs(item).isBefore(new Date())) {
    return h(Badge, {
      label: "Failed",
      theme: "red",
      variant: "outline",
    });
  }
  if (row.first_responded_on && dayjs(row.first_responded_on).isBefore(item)) {
    return h(Badge, {
      label: "Fulfilled",
      theme: "green",
      variant: "outline",
    });
  } else if (dayjs(row.first_responded_on).isAfter(item)) {
    return h(Badge, {
      label: "Failed",
      theme: "red",
      variant: "outline",
    });
  } else {
    return h(
      Tooltip,
      {
        text: dayjs(item).long(),
      },
      () => dayjs.tz(item).fromNow()
    );
  }
}

function handle_resolution_by_field(row: any, item: string) {
  const status = getStatus(row.status) || {};
  if (status.category === "Paused") {
    return h(Badge, {
      label: "Paused",
      theme: "blue",
      variant: "outline",
    });
  } else if (row.resolution_date && dayjs(row.resolution_date).isBefore(item)) {
    return h(Badge, {
      label: "Fulfilled",
      theme: "green",
      variant: "outline",
    });
  } else if (dayjs(row.resolution_date).isAfter(item)) {
    return h(Badge, {
      label: "Failed",
      theme: "red",
      variant: "outline",
    });
  } else {
    return h(
      Tooltip,
      {
        text: dayjs(item).long(),
      },
      () => dayjs.tz(item).fromNow()
    );
  }
}

async function exportRows(
  export_type: "CSV" | "Excel" = "Excel",
  export_all: boolean = false
) {
  const list = listViewRef.value?.list;
  if (!list) return;

  const fields = JSON.stringify(list.data.columns.map((f) => f.key));
  const order_by = list.params.order_by;

  let filters = { ...list.params.filters };
  let pageLength: number;

  if (export_all) {
    filters = JSON.stringify(filters);
    pageLength = list.data.total_count;
  } else {
    pageLength = listSelections.value.size;
    filters["name"] = ["in", Array.from(listSelections.value)];
    filters = JSON.stringify(filters);
  }

  window.location.href = `/api/method/frappe.desk.reportview.export_query?file_format_type=${export_type}&title=HD Ticket&doctype=HD Ticket&fields=${fields}&filters=${filters}&order_by=${order_by}&page_length=${pageLength}&start=0&view=Report&with_comment_count=1`;
  reset();
  showExportModal.value = false;
}

function reset(reload = false) {
  listViewRef.value?.unselectAll();
  listSelections.value?.clear();
  if (reload) listViewRef.value.reload();
}

const pageLengthCount = computed(
  () =>
    listViewRef.value?.list?.params?.page_length_count ||
    options.default_page_length ||
    20
);

function handleCardLoadMore() {
  const count = pageLengthCount.value;
  listViewRef.value?.handlePageLength?.(count, true);
}

function statusRank(row: any) {
  const meta = getStatus(row?.status) || {};
  const category = meta.category || "";
  if (category === "Resolved") return 3;
  if (category === "Paused") return 1;
  return 0;
}

function handleCardClick(ticketId: string) {
  console.log("Navigating to ticket:", ticketId);
  if (!ticketId) {
    console.error("No ticket ID provided");
    return;
  }
  router.push({
    name: isCustomerPortal.value ? "TicketCustomer" : "TicketAgent",
    params: { ticketId },
  });
}

function handleCardStatus(ticketId: string, value: string) {
  updateTicketField(ticketId, "status", value);
}

function handleCardPriority(ticketId: string, value: string) {
  updateTicketField(ticketId, "priority", value);
}

function applyCardFilters() {
  if (!listViewRef.value?.list) return;
  const list = listViewRef.value.list;
  const filters = { ...(list.params?.filters || {}) };

  if (cardFilters.status.length) {
    filters["status"] = ["in", cardFilters.status];
  } else {
    delete filters["status"];
  }

  if (cardFilters.priority.length) {
    filters["priority"] = ["in", cardFilters.priority];
  } else {
    delete filters["priority"];
  }

  if (cardFilters.department.length) {
    filters["department"] = ["in", cardFilters.department];
  } else {
    delete filters["department"];
  }

  if (cardFilters.agent.length) {
    filters["assigned_to"] = ["in", cardFilters.agent];
  } else {
    delete filters["assigned_to"];
  }

  list.submit({
    ...list.params,
    filters,
  });
}

function resetCardFilters() {
  cardFilters.status = [];
  cardFilters.priority = [];
  cardFilters.department = [];
  cardFilters.agent = [];
  activeQuickView.value = "";
  applyCardFilters();
}

function applyQuickView(view: any) {
  if (!listViewRef.value?.list) return;
  
  // Reset existing filters first
  resetCardFilters();
  
  // Set active quick view
  activeQuickView.value = view.label;
  
  // Apply the quick view filters directly to the list
  const list = listViewRef.value.list;
  list.submit({
    ...list.params,
    filters: view.filters,
  });
}

function toggleValue(arr: string[], value: string) {
  return arr.includes(value) ? arr.filter((v) => v !== value) : [...arr, value];
}

const slaStatusColorMap = {
  Fulfilled: "green",
  Failed: "red",
  "Resolution Due": "orange",
  "First Response Due": "orange",
  Paused: "blue",
};

let viewDialog = reactive({
  show: false,
  view: {
    label: "",
    icon: "",
    name: "",
  },
  mode: "create",
});

const dropdownOptions = computed(() => {
  const items = [
    {
      group: "Default Views",
      items: [
        {
          label: "List View",
          icon: "align-justify",
          onClick: () =>
            router.push({
              name: isCustomerPortal.value ? "TicketsCustomer" : "TicketsAgent",
            }),
        },
      ],
    },
  ];

  // Saved Views
  if (getCurrentUserViews.value?.length !== 0) {
    items.push({
      group: "Saved Views",
      items: parseViews(getCurrentUserViews.value),
    });
  }
  if (pinnedViews.value?.length !== 0) {
    items.push({
      group: "Private Views",
      items: parseViews(pinnedViews.value),
    });
  }
  if (publicViews.value?.length !== 0) {
    items.push({
      group: "Public Views",
      items: parseViews(publicViews.value),
    });
  }

  items.push({
    group: "Create View",
    hideLabel: true,
    items: [
      {
        label: "Create View",
        icon: "plus",
        onClick: () => {
          resetState();
          viewDialog.show = true;
        },
      },
    ],
  });

  return items;
});

let selectedView: View | null = null;

const viewActions = (view) => {
  const _view = findView(view.name).value;

  let actions = [
    {
      group: "Default Views",
      hideLabel: true,
      items: [
        {
          label: "Duplicate",
          icon: h(FeatherIcon, { name: "copy" }),
          onClick: () => {
            viewDialog.view.label = _view.label + " (New)";
            viewDialog.view.icon = _view.icon;
            viewDialog.view.name = _view.name;
            viewDialog.mode = "duplicate";
            selectedView = _view;
            viewDialog.show = true;
          },
        },
      ],
    },
  ];
  if (!_view.public || isManager) {
    actions[0].items.push({
      label: "Edit",
      icon: h(EditIcon, { class: "h-4 w-4" }),
      onClick: () => {
        viewDialog.view.label = _view.label;
        viewDialog.view.icon = _view.icon;
        viewDialog.view.name = _view.name;
        viewDialog.mode = "edit";
        viewDialog.show = true;
      },
    });
    if (!_view.public) {
      actions[0].items.push({
        label: _view?.pinned ? "Unpin View" : "Pin View",
        icon: h(_view?.pinned ? UnpinIcon : PinIcon, { class: "h-4 w-4" }),
        onClick: () => {
          const newView = {
            name: _view.name,
          };
          newView["pinned"] = !_view.pinned;
          updateView(newView);
        },
      });
    }
    if (isManager && !isCustomerPortal.value) {
      actions[0].items.push({
        label: _view?.public ? "Make Private" : "Make Public",
        icon: h(FeatherIcon, {
          name: _view?.public ? "lock" : "unlock",
          class: "h-4 w-4",
        }),
        onClick: () => {
          const newView = {
            name: _view.name,
            public: !_view.public,
          };

          if (_view.public) {
            $dialog({
              title: `Make ${_view.label} private?`,
              message:
                "This view is currently public. Changing it to private will hide it for all the users.",
              actions: [
                {
                  label: "Confirm",
                  variant: "solid",
                  onClick({ close }) {
                    close();
                    updateView(newView);
                  },
                },
              ],
            });
          } else {
            updateView(newView);
          }
        },
      });
    }
    actions.push({
      group: "Delete View",
      hideLabel: true,
      items: [
        {
          label: "Delete",
          icon: "trash-2",
          onClick: () => {
            $dialog({
              title: `Delete ${_view.label}?`,
              message: `Are you sure you want to delete this view?
              ${
                _view.public
                  ? "This view is public, and will be removed for all users."
                  : ""
              }`,
              actions: [
                {
                  label: "Confirm",
                  variant: "solid",
                  onClick({ close }) {
                    if (route.query.view === _view.name) {
                      router.push({
                        name: isCustomerPortal.value
                          ? "TicketsCustomer"
                          : "TicketsAgent",
                      });
                    }
                    deleteView(_view.name);
                    handleSuccess("deleted");
                    close();
                  },
                },
              ],
            });
          },
        },
      ],
    });
  }

  return actions;
};

function parseViews(views: View[]) {
  return views?.map((view) => {
    return {
      ...view,
      onClick: () => {
        currentView.value = {
          label: view.label,
          icon: view.icon,
        };
        router.push({
          name: view.route_name,
          query: {
            view: view.name,
          },
        });
      },
    };
  });
}

function handleView(viewInfo, action) {
  let view: View;
  if (action === "update") {
    updateView(viewInfo);
    handleSuccess("updated");
    currentView.value = {
      label: viewInfo.label,
      icon: getIcon(viewInfo.icon),
    };
    return;
  } else if (action === "duplicate") {
    view = {
      ...selectedView,
      filters: JSON.stringify(selectedView.filters),
      columns: JSON.stringify(selectedView.columns),
      rows: JSON.stringify(selectedView.rows),
      label: viewInfo.label,
      icon: viewInfo.icon,
      public: false,
      pinned: false,
    };
  } else {
    view = {
      dt: "HD Ticket",
      type: "list",
      label: viewInfo.label ?? "List",
      icon: viewInfo.icon ?? "",
      route_name: router.currentRoute.value.name as string,
      order_by: listViewRef.value?.list?.params.order_by,
      filters: JSON.stringify(listViewRef.value?.list?.params.filters),
      columns: JSON.stringify(listViewRef.value?.list?.data.columns),
      rows: JSON.stringify(listViewRef.value?.list?.data?.rows),
      is_customer_portal: isCustomerPortal.value,
    };
  }

  // createView
  createView(view, (d) => {
    currentView.value = {
      label: d.label || "List",
      icon: getIcon(d.icon),
    };
    router.push({
      name: isCustomerPortal.value ? "TicketsCustomer" : "TicketsAgent",
      query: {
        view: d.name,
      },
    });

    handleSuccess();
  });
}

function handleSuccess(msg = "created") {
  toast.success(`View ${msg}`);
  resetState();
}
function resetState() {
  viewDialog.show = false;
  viewDialog.view.label = "";
  viewDialog.view.icon = "";
  viewDialog.view.name = "";
  viewDialog.mode = null;
  selectedView = null;
}

// Watch viewMode and reset filters when switching to card view
watch(viewMode, (newMode, oldMode) => {
  if (newMode === 'card' && oldMode === 'table') {
    resetCardFilters();
  }
});

onMounted(() => {
  if (!route.query.view) {
    currentView.value = {
      label: "List",
      icon: LucideAlignJustify,
    };
  }
  if (!isCustomerPortal.value) {
    $socket.on("helpdesk:new-ticket", () => {
      listViewRef.value?.reload();
    });
  }
});

onUnmounted(() => {
  if (!isCustomerPortal.value) {
    $socket.off("helpdesk:new-ticket");
  }
});

usePageMeta(() => {
  return {
    title: "Tickets",
  };
});
</script>
