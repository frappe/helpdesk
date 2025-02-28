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
        <RouterLink
          :to="{ name: isCustomerPortal ? 'TicketNew' : 'TicketAgentNew' }"
        >
          <Button label="Create" theme="gray" variant="solid">
            <template #prefix>
              <LucidePlus class="h-4 w-4" />
            </template>
          </Button>
        </RouterLink>
      </template>
    </LayoutHeader>
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
import { h, ref, computed, reactive, onMounted } from "vue";
import {
  Badge,
  Tooltip,
  confirmDialog,
  call,
  usePageMeta,
  FeatherIcon,
} from "frappe-ui";
import { useRouter, useRoute } from "vue-router";
import {
  EditIcon,
  IndicatorIcon,
  PinIcon,
  UnpinIcon,
} from "@/components/icons";
import { LayoutHeader, ListViewBuilder } from "@/components";
import ExportModal from "@/components/ticket/ExportModal.vue";
import ViewBreadcrumbs from "@/components/ViewBreadcrumbs.vue";
import ViewModal from "@/components/ViewModal.vue";
import { useTicketStatusStore } from "@/stores/ticketStatus";
import { useAuthStore } from "@/stores/auth";
import { dayjs } from "@/dayjs";
import { createToast, getIcon, isCustomerPortal } from "@/utils";
import { capture } from "@/telemetry";
import { TicketIcon } from "@/components/icons";
import { useView, currentView } from "@/composables/useView";
import { View } from "@/types";

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

const { isManager } = useAuthStore();

const listViewRef = ref(null);
const showExportModal = ref(false);

const { textColorMap } = useTicketStatusStore();

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
  {
    label: "Delete",
    icon: "trash-2",
    onClick: (selections: Set<string>) => {
      listSelections.value = new Set(selections);
      confirmDialog({
        title: "Delete Ticket(s)?",
        message: `Are you sure you want to delete these ticket(s)?`,
        onConfirm: ({ hideDialog }: { hideDialog: Function }) => {
          hideDialog();
          handleTicketDelete(hideDialog);
        },
      });
    },
    condition: () => !isCustomerPortal.value && isManager,
  },
];

function handleTicketDelete(hide: Function) {
  capture("bulk_delete");
  call("frappe.desk.reportview.delete_items", {
    items: JSON.stringify(Array.from(listSelections.value)),
    doctype: "HD Ticket",
  }).then(() => {
    createToast({
      title: "Deleted successfully",
      icon: "check",
      iconClasses: "text-ink-green-3",
    });
    hide();
    reset(true);
  });
}

const options = {
  doctype: "HD Ticket",
  columnConfig: {
    status: {
      prefix: ({ row }) => {
        return h(IndicatorIcon, {
          class: textColorMap[row.status],
        });
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
  if (row.resolution_date && dayjs(row.resolution_date).isBefore(item)) {
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

const slaStatusColorMap = {
  Fulfilled: "green",
  Failed: "red",
  "Resolution Due": "orange",
  "First Response Due": "orange",
  Paused: "blue",
};

const viewDialog = reactive({
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
            confirmDialog({
              title: `Make ${_view.label} private?`,
              message:
                "This view is currently public. Changing it to private will hide it for all the users.",
              onConfirm: ({ hideDialog }: { hideDialog: Function }) => {
                hideDialog();
                updateView(newView);
              },
            });
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
            confirmDialog({
              title: `Delete ${_view.label}?`,
              message: `Are you sure you want to delete this view?
              ${
                _view.public
                  ? "This view is public, and will be removed for all users."
                  : ""
              }`,
              onConfirm: ({ hideDialog }: { hideDialog: Function }) => {
                if (route.query.view === _view.name) {
                  router.push({
                    name: isCustomerPortal.value
                      ? "TicketsCustomer"
                      : "TicketsAgent",
                  });
                }
                deleteView(_view.name);
                handleSuccess("deleted");
                hideDialog();
              },
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
  createToast({
    title: `View ${msg} successfully`,
    icon: "check",
    iconClasses: "text-green-600",
  });
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

onMounted(() => {
  if (!route.query.view) {
    currentView.value = {
      label: "List",
      icon: "lucide:align-justify",
    };
  }
});
usePageMeta(() => {
  return {
    title: "Tickets",
  };
});
</script>
