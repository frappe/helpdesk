<template>
  <div>
    <LayoutHeader>
      <template #left-header>
        <ViewBreadcrumbs
          :label="__('Tickets')"
          :route-name="isCustomerPortal ? 'TicketsCustomer' : 'TicketsAgent'"
          :options="dropdownOptions"
          :dropdown-actions="(view) => viewActions(view, viewDialogConfig)"
          :current-view="currentView"
        />
      </template>
      <template #right-header>
        <RouterLink
          class="inline-flex"
          :to="{ name: isCustomerPortal ? 'TicketNew' : 'TicketAgentNew' }"
        >
          <Button
            class="rtl:flex-row-reverse"
            :label="__('Create')"
            theme="gray"
            variant="solid"
          >
            <template #prefix>
              <LucidePlus class="h-4 w-4" />
            </template>
          </Button>
        </RouterLink>
      </template>
    </LayoutHeader>
    <!-- Custom Filter Bar (Agent View only) -->
    <div
      v-if="!isCustomerPortal"
      class="flex flex-wrap items-center gap-3 px-5 py-3 border-b bg-white select-none"
    >
      <!-- Search Input -->
      <div class="flex-1 min-w-[200px]">
        <TextInput
          v-model="filtersState.search"
          type="text"
          :placeholder="__('Search by ID or Subject...')"
          @input="debouncedFilterChange"
        >
          <template #prefix>
            <LucideSearch class="h-4 w-4 text-ink-gray-4" />
          </template>
        </TextInput>
      </div>

      <!-- Priority Filter -->
      <div class="w-[160px]">
        <FormControl
          type="select"
          :model-value="filtersState.priority"
          :options="priorityOptions"
          :placeholder="__('Priority')"
          @update:modelValue="(val) => { filtersState.priority = val; onFilterChange(); }"
        />
      </div>

      <!-- Status Filter -->
      <div class="w-[160px]">
        <FormControl
          type="select"
          :model-value="filtersState.status"
          :options="statusOptions"
          :placeholder="__('Status')"
          @update:modelValue="(val) => { filtersState.status = val; onFilterChange(); }"
        />
      </div>

      <!-- Assignee Filter -->
      <div class="w-[180px]">
        <Link
          doctype="User"
          :value="filtersState.assignee"
          :placeholder="__('Assignee')"
          @change="(val) => { filtersState.assignee = val; onFilterChange(); }"
        />
      </div>

      <!-- Date Preset Filter -->
      <div class="w-[160px]">
        <FormControl
          type="select"
          :model-value="filtersState.datePreset"
          :options="datePresetOptions"
          :placeholder="__('Date Created')"
          @update:modelValue="onDatePresetChange"
        />
      </div>

      <!-- Custom Date Picker -->
      <div v-if="filtersState.datePreset === 'custom'" class="w-[160px]">
        <DatePicker
          :value="filtersState.customDate"
          @change="(val) => { filtersState.customDate = val; onFilterChange(); }"
          :placeholder="__('Pick Date')"
        />
      </div>

      <!-- Clear Filters Button -->
      <Button
        v-if="hasCustomFilters"
        variant="subtle"
        theme="gray"
        @click="clearCustomFilters"
      >
        {{ __('Clear') }}
      </Button>
    </div>
    <ListViewBuilder
      ref="listViewRef"
      :options="options"
      @row-click="
        (row) =>
          $router.push({
            name: isCustomerPortal ? 'TicketCustomer' : 'TicketAgent',
            params: { ticketId: row },
          })
      "
    />
    <ExportModal
      v-model="showExportModal"
      :rowCount="$refs.listViewRef?.list?.data?.total_count ?? 0"
      @update="
        ({ export_type, export_all }) => exportRows(export_type, export_all)
      "
    />
    <ViewModal
      v-if="viewDialogConfig.show"
      v-model="viewDialogConfig"
      @update="onViewModalUpdate"
    />
    <BulkReplyModal
      v-model="showBulkReplyModal"
      :selections="listSelections"
      @success="listViewRef?.unselectAll()"
    />
  </div>
</template>

<script setup lang="ts">
import { LayoutHeader, ListViewBuilder, Link } from "@/components";
import { TicketIcon } from "@/components/icons";
import IndicatorIcon from "@/components/icons/IndicatorIcon.vue";
import BulkReplyModal from "@/components/ticket-agent/BulkReplyModal.vue";
import ExportModal from "@/components/ticket/ExportModal.vue";
import ViewBreadcrumbs from "@/components/ViewBreadcrumbs.vue";
import { normalizeFilters } from "@/components/view-controls/filter";
import ViewModal from "@/components/ViewModal.vue";
import { currentView, useView } from "@/composables/useView";
import { useAuthStore } from "@/stores/auth";
import { globalStore } from "@/stores/globalStore";
import { useTicketStatusStore } from "@/stores/ticketStatus";
import { __ } from "@/translation";
import { View } from "@/types";
import { isCustomerPortal, shortDuration } from "@/utils";
import { Badge, dayjs, Tooltip, usePageMeta, DatePicker, FormControl, TextInput, createListResource } from "frappe-ui";
import { computed, h, onMounted, onUnmounted, reactive, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import { useDebounceFn } from "@vueuse/core";

const router = useRouter();
const route = useRoute();

const {
  getCurrentUserViews,
  publicViews,
  pinnedViews,
  findView,
  standardViews,
  viewActions,
  handleView,
  resetViewDialog,
} = useView("HD Ticket");

const activeView = computed(() => findView(route.query.view as string).value);
const hasActiveFilters = computed(
  () => Object.keys(listViewRef.value?.list?.params?.filters || {}).length > 0
);

const { $socket } = globalStore();
const { isManager, userId } = useAuthStore();

const listViewRef = ref(null);

const filtersState = reactive({
  search: "",
  priority: "",
  status: "",
  assignee: "",
  datePreset: "",
  customDate: "",
});

const isSyncing = ref(false);

const priorities = createListResource({
  doctype: "HD Ticket Priority",
  fields: ["name"],
  auto: true,
});

const priorityOptions = computed(() => {
  if (!priorities.data) return [];
  const opts = priorities.data.map((p: any) => ({
    label: p.name,
    value: p.name,
  }));
  return [{ label: __("All Priorities"), value: "" }, ...opts];
});

const statusStore = useTicketStatusStore();
const statusOptions = computed(() => {
  if (!statusStore.statuses.data) return [];
  const opts = statusStore.statuses.data.map((s: any) => ({
    label: s.label_agent,
    value: s.name,
  }));
  return [{ label: __("All Statuses"), value: "" }, ...opts];
});

const datePresetOptions = [
  { label: __("All Dates"), value: "" },
  { label: __("Today"), value: "today" },
  { label: __("Yesterday"), value: "yesterday" },
  { label: __("This Week"), value: "this_week" },
  { label: __("This Month"), value: "this_month" },
  { label: __("Custom..."), value: "custom" },
];

const hasCustomFilters = computed(() => {
  return (
    filtersState.search ||
    filtersState.priority ||
    filtersState.status ||
    filtersState.assignee ||
    filtersState.datePreset
  );
});

function onDatePresetChange(val: string) {
  filtersState.datePreset = val;
  if (val !== "custom") {
    filtersState.customDate = "";
  }
  onFilterChange();
}

function clearCustomFilters() {
  filtersState.search = "";
  filtersState.priority = "";
  filtersState.status = "";
  filtersState.assignee = "";
  filtersState.datePreset = "";
  filtersState.customDate = "";
  onFilterChange();
}

const debouncedFilterChange = useDebounceFn(() => {
  onFilterChange();
}, 400);

function onFilterChange() {
  if (isSyncing.value) return;

  const currentFilters = listViewRef.value?.list?.params?.filters || [];
  const controlledFields = ["_search", "priority", "status", "_assign", "creation"];

  let mergedFilters = currentFilters.filter(
    (c: any) => Array.isArray(c) && !controlledFields.includes(c[0])
  );

  if (filtersState.search) {
    mergedFilters.push(["_search", "like", filtersState.search]);
  }

  if (filtersState.priority) {
    mergedFilters.push(["priority", "=", filtersState.priority]);
  }

  if (filtersState.status) {
    mergedFilters.push(["status", "=", filtersState.status]);
  }

  if (filtersState.assignee) {
    mergedFilters.push(["_assign", "like", `%${filtersState.assignee}%`]);
  }

  if (filtersState.datePreset) {
    if (filtersState.datePreset === "today") {
      mergedFilters.push(["creation", ">=", dayjs().startOf("day").format("YYYY-MM-DD HH:mm:ss")]);
      mergedFilters.push(["creation", "<=", dayjs().endOf("day").format("YYYY-MM-DD HH:mm:ss")]);
    } else if (filtersState.datePreset === "yesterday") {
      mergedFilters.push(["creation", ">=", dayjs().subtract(1, "day").startOf("day").format("YYYY-MM-DD HH:mm:ss")]);
      mergedFilters.push(["creation", "<=", dayjs().subtract(1, "day").endOf("day").format("YYYY-MM-DD HH:mm:ss")]);
    } else if (filtersState.datePreset === "this_week") {
      mergedFilters.push(["creation", ">=", dayjs().startOf("week").format("YYYY-MM-DD HH:mm:ss")]);
      mergedFilters.push(["creation", "<=", dayjs().endOf("week").format("YYYY-MM-DD HH:mm:ss")]);
    } else if (filtersState.datePreset === "this_month") {
      mergedFilters.push(["creation", ">=", dayjs().startOf("month").format("YYYY-MM-DD HH:mm:ss")]);
      mergedFilters.push(["creation", "<=", dayjs().endOf("month").format("YYYY-MM-DD HH:mm:ss")]);
    } else if (filtersState.datePreset === "custom" && filtersState.customDate) {
      mergedFilters.push(["creation", ">=", dayjs(filtersState.customDate).startOf("day").format("YYYY-MM-DD HH:mm:ss")]);
      mergedFilters.push(["creation", "<=", dayjs(filtersState.customDate).endOf("day").format("YYYY-MM-DD HH:mm:ss")]);
    }
  }

  listViewRef.value?.applyFilters(mergedFilters);
}

watch(
  () => listViewRef.value?.list?.params?.filters,
  (newFilters) => {
    if (isSyncing.value) return;
    isSyncing.value = true;

    filtersState.search = "";
    filtersState.priority = "";
    filtersState.status = "";
    filtersState.assignee = "";
    filtersState.datePreset = "";
    filtersState.customDate = "";

    if (newFilters && Array.isArray(newFilters)) {
      for (const condition of newFilters) {
        if (!Array.isArray(condition)) continue;
        const [field, op, val] = condition;
        if (field === "_search") {
          filtersState.search = val;
        } else if (field === "priority") {
          filtersState.priority = val;
        } else if (field === "status") {
          filtersState.status = val;
        } else if (field === "_assign") {
          if (typeof val === "string") {
            filtersState.assignee = val.replaceAll("%", "");
          }
        }
      }
    }
    isSyncing.value = false;
  },
  { deep: true }
);
const showExportModal = ref(false);

const { getStatus } = useTicketStatusStore();

const listSelections = ref(new Set());

const showBulkReplyModal = ref(false);

const selectBannerActions = [
  {
    label: __("Bulk Reply"),
    icon: "lucide-corner-up-left",
    onClick: (selections: Set<string>) => {
      listSelections.value = new Set(selections);
      showBulkReplyModal.value = true;
    },
  },
  {
    label: __("Export"),
    icon: "lucide-download",
    onClick: (selections: Set<string>) => {
      listSelections.value = new Set(selections);
      showExportModal.value = true;
    },
  },
];

const options = computed(() => ({
  doctype: "HD Ticket",
  columnConfig: {
    subject: {
      custom: ({ row, item }) => {
        const seenBy = row._seen ? JSON.parse(row._seen) : [];
        const isSeen = seenBy.includes(userId || "");
        return h(
          "span",
          {
            class: ["truncate flex-1", !isSeen && "font-semibold"],
          },
          item
        );
      },
    },
    status: {
      custom: ({ item }) => {
        const status = getStatus(item);
        const label = isCustomerPortal.value
          ? status?.["label_customer"]
          : status?.["label_agent"];
        return h(
          "div",
          { class: "flex items-center gap-1.5 justify-start w-full" },
          [
            h(IndicatorIcon, { class: status?.["parsed_color"] }),
            h("span", { class: "truncate flex-1 text-base" }, label),
          ]
        );
      },
    },
    agreement_status: {
      custom: ({ item }) => {
        return h(Badge, {
          label: __(item),
          theme: slaStatusColorMap[item],
          variant: "subtle",
        });
      },
    },
    response_by: {
      custom: ({ row, item }) => handleResponseByField(row, item),
    },
    resolution_by: {
      custom: ({ row, item }) => handleResolutionByField(row, item),
    },
  },
  isCustomerPortal: isCustomerPortal.value,
  selectable: true,
  showSelectBanner: true,
  selectBannerActions,
  emptyState: {
    title: __("No tickets found"),
    icon: h(TicketIcon, {
      class: "h-10 w-10",
    }),
    description:
      activeView.value?.public || activeView.value?.pinned
        ? __(
            "No tickets found for this view. Try adjusting your filters or creating a new view."
          )
        : hasActiveFilters.value
        ? __(
            "No tickets found for the applied filters. Try adjusting or clearing your filters."
          )
        : undefined,
  },
  rowRoute: {
    name: isCustomerPortal.value ? "TicketCustomer" : "TicketAgent",
    prop: "ticketId",
  },
  hideColumnSetting: false,
  hideQuickFilters: !isCustomerPortal.value,
}));

function handleResponseByField(row: any, item: string) {
  if (!row.first_responded_on && dayjs(item).isBefore(new Date())) {
    return h(Badge, {
      label: __("Failed"),
      theme: "red",
      variant: "subtle",
    });
  }
  if (row.first_responded_on && dayjs(row.first_responded_on).isBefore(item)) {
    return h(Badge, {
      label: __("Fulfilled"),
      theme: "gray",
      variant: "subtle",
    });
  } else if (dayjs(row.first_responded_on).isAfter(item)) {
    return h(Badge, {
      label: __("Failed"),
      theme: "red",
      variant: "subtle",
    });
  } else {
    return h(
      Tooltip,
      {
        text: dayjs(item).format("LLLL"),
      },
      h(Badge, {
        label: shortDuration(item),
        variant: "subtle",
        theme: "orange",
      })
    );
  }
}

function handleResolutionByField(row: any, item: string) {
  const status = getStatus(row.status) || {};
  if (status.category === "Paused") {
    return h(Badge, {
      label: __("Paused"),
      theme: "blue",
      variant: "subtle",
    });
  }
  if (row.resolution_date) {
    const fulfilled = dayjs(row.resolution_date).isBefore(
      dayjs(row.resolution_by)
    );
    return h(Badge, {
      label: fulfilled ? __("Fulfilled") : __("Failed"),
      theme: fulfilled ? "gray" : "red",
      variant: "subtle",
    });
  }
  // In progress but the resolution deadline has already passed.
  if (dayjs(item).isBefore(dayjs())) {
    return h(Badge, {
      label: __("Failed"),
      theme: "red",
      variant: "subtle",
    });
  }
  // In progress with a future deadline: show the live countdown.
  return h(
    Tooltip,
    {
      text: dayjs(item).format("LLLL"),
    },
    h(Badge, {
      label: shortDuration(item),
      variant: "subtle",
      theme: "orange",
    })
  );
}

async function exportRows(
  export_type: "CSV" | "Excel" = "Excel",
  export_all: boolean = false
) {
  const list = listViewRef.value?.list;
  if (!list) return;

  const fields = JSON.stringify(list.data.columns.map((f) => f.key));
  const order_by = list.params.order_by;

  // Resolve `@me` filters to the current session user before export
  const resolveAtMe = (entry: any) => {
    if (Array.isArray(entry)) return entry.map(resolveAtMe);
    if (entry === "@me") return userId;
    if (entry === "%@me%") return `%${userId}%`;
    return entry;
  };
  const conditions = normalizeFilters(list.params.filters).map(
    ([field, operator, value]) => [field, operator, resolveAtMe(value)]
  );
  let pageLength: number;

  if (export_all) {
    pageLength = list.data.total_count;
  } else {
    pageLength = listSelections.value.size;
    conditions.push(["name", "in", Array.from(listSelections.value)]);
  }
  const filters = JSON.stringify(conditions);

  window.location.href = `/api/method/frappe.desk.reportview.export_query?file_format_type=${export_type}&title=HD Ticket&doctype=HD Ticket&fields=${fields}&filters=${encodeURIComponent(
    filters
  )}&order_by=${order_by}&page_length=${pageLength}&start=0&view=Report&with_comment_count=1`;
  reset();
  showExportModal.value = false;
}

function reset(reload = false) {
  listViewRef.value?.unselectAll();
  listSelections.value?.clear();
  if (reload) listViewRef.value.reload();
}

const slaStatusColorMap = {
  Fulfilled: "gray",
  Failed: "red",
  "Resolution Due": "orange",
  "First Response Due": "orange",
  Paused: "blue",
};

let viewDialogConfig = reactive({
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
      group: __("Default Views"),
      items: [
        {
          label: __("List View"),
          icon: "lucide-align-justify",
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
      group: __("Saved Views"),
      items: parseViews(getCurrentUserViews.value),
    });
  }
  if (pinnedViews.value?.length !== 0) {
    items.push({
      group: __("Private Views"),
      items: parseViews(pinnedViews.value),
    });
  }

  const allPublicViews = [
    ...(standardViews.value || []),
    ...(publicViews.value || []),
  ];

  const uniquePublicViews = Array.from(
    new Map(allPublicViews.map((v) => [v.name, v])).values()
  );

  items.push({
    group: __("Public Views"),
    items: parseViews(uniquePublicViews),
  });

  items.push({
    group: __("Create View"),
    hideLabel: true,
    items: [
      {
        label: __("Create View"),
        icon: "lucide-plus",
        onClick: () => {
          resetViewDialog(viewDialogConfig);
          viewDialogConfig.show = true;
        },
      },
    ],
  });

  return items;
});

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

function onViewModalUpdate(viewInfo: any, action: string) {
  handleView(viewInfo, action, viewDialogConfig, () => listViewRef.value?.list);
}

onMounted(() => {
  if (!route.query.view) {
    currentView.value = {
      label: __("List"),
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
    title: __("Tickets"),
  };
});
</script>
