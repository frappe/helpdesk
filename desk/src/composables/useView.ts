import { EditIcon, PinIcon, UnpinIcon } from "@/components/icons";
import { useAuthStore } from "@/stores/auth";
import { globalStore } from "@/stores/globalStore";
import { __ } from "@/translation";
import { View } from "@/types";
import { getIcon, isCustomerPortal } from "@/utils";
import { useDebounceFn } from "@vueuse/core";
import {
  call,
  createListResource,
  createResource,
  FeatherIcon,
  toast,
} from "frappe-ui";
import { computed, h, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";

const debouncedSetValue = useDebounceFn(
  (doctype: string, name: string, fieldname: any, cb?: Function) => {
    call("frappe.client.set_value", { doctype, name, fieldname }).then(() => {
      cb?.();
      views.reload();
    });
  },
  300
);


export const views = createListResource({
  doctype: "HD View",
  fields: ["*"],
  transform: (data: any) => {
    data.forEach((view: View) => {
      view.filters = JSON.parse(view.filters) || {};
      view.columns = JSON.parse(view.columns) || [];
      view.rows = JSON.parse(view.rows) || [];
    });
  },
  pageLength: 1000,
});

export const currentView = ref({
  label: "List",
  icon: LucideAlignJustify,
});

export function useView(dt: string = null) {
  const auth = useAuthStore();
  const router = useRouter();
  const route = useRoute();
  const { $dialog } = globalStore();
  function callGetViews() {
    if (
      (views.filters?.dt === dt && views.data?.length > 0) ||
      views.list?.promise
      // views.isCustomerPortal === isCustomerPortal.value
    ) {
      return;
    }
    const filters = {
      is_customer_portal: isCustomerPortal.value,
    };
    if (dt) {
      filters["dt"] = dt;
    }
    if (isCustomerPortal.value) {
      filters["user"] = auth.userId;
    }
    views.isCustomerPortal = isCustomerPortal.value;
    views.update({ filters });
    views.fetch();
  }
  callGetViews();

  const getCurrentUserViews = computed(() =>
    views.data
      ?.filter(
        (view: View) =>
          !view.is_default &&
          view.user === auth.userId &&
          !view.public &&
          !view.pinned &&
          !view.is_standard
      )
      .map(parseView)
  );

  async function createView(
    view: View,
    successCB: Function = () => {},
    errorCB: Function = () => {}
  ) {
    createResource({
      url: "frappe.client.insert",
      params: {
        doc: {
          doctype: "HD View",
          ...view,
          user: auth.userId,
        },
      },
      auto: true,
      onSuccess: (d) => {
        views.reload().then(() => {
          successCB(d);
        });
      },
      onError: (e) => {
        console.log("error", e);
        errorCB(e);
      },
    });
  }

  function findView(viewName: string) {
    return computed(() => views.data?.find((v: View) => v.name === viewName));
  }

  const pinnedViews = computed(() =>
    views.data
      ?.filter((view: View) => view.pinned && view.user === auth.userId)
      .map(parseView)
  );

  const publicViews = computed(() =>
    views.data?.filter((view: View) => view.public).map(parseView)
  );

  const defaultView = computed(() =>
    views.data?.find(
      (v: View) => v.is_default && v.user === auth.userId && v.dt === dt
    )
  );

  const standardViews = computed(() =>
    views.data?.filter((view: View) => view.is_standard).map(parseView)
  );

  function updateView(view: any, successCB: Function = () => {}) {
    if (view.name !== "default") {
      // handle custom view
      debouncedSetValue("HD View", view.name, view, successCB);
    } else {
      // handle default view
      createOrUpdateDefaultView(view);
      successCB();
    }
  }

  function deleteView(viewName: string) {
    call("frappe.client.delete", {
      doctype: "HD View",
      name: viewName,
    }).then(() => {
      views.reload();
    });
  }

  function createOrUpdateDefaultView(view: View) {
    const defaultView = views.data?.find(
      (v: View) => v.is_default && v.user === auth.userId && v.dt === view.dt
    );
    view.is_customer_portal = isCustomerPortal.value;
    if (defaultView) {
      delete view["name"];

       debouncedSetValue("HD View", defaultView.name, view);
    } else {
      view["doctype"] = "HD View";
      // create default view
      createView({
        ...view,
        is_default: true,
      });
    }
  }

  function parseView(view: View) {
    return {
      label: view.label,
      name: view.name,
      icon: getIcon(view.icon),
      route_name: view.route_name,
      is_standard: view.is_standard || false,
      onClick: () => {
        router.push({
          name: view.route_name,
          query: {
            view: view.name,
          },
        });
      },
    };
  }

  // Kebab-menu actions for a single view. Shared between the breadcrumb dropdown
  // and the sidebar so both expose the same options. `viewDialogConfig` is the caller's
  // reactive modal state, populated here for the edit/duplicate flows.
  function viewActions(view: View, viewDialogConfig: any) {
    const _view = findView(view.name).value;

    const actions: any[] = [
      {
        group: __("Default Views"),
        hideLabel: true,
        items: [
          {
            label: __("Duplicate"),
            icon: h(FeatherIcon, { name: "copy" }),
            onClick: () => {
              viewDialogConfig.view.label = _view.label + " (New)";
              viewDialogConfig.view.icon = _view.icon;
              viewDialogConfig.view.name = _view.name;
              viewDialogConfig.mode = "duplicate";
              viewDialogConfig.show = true;
            },
          },
        ],
      },
    ];

    if (!_view.public || auth.isManager) {
      if (!_view.public && !_view.is_standard) {
        actions[0].items.push({
          label: _view?.pinned ? __("Unpin View") : __("Pin View"),
          icon: h(_view?.pinned ? UnpinIcon : PinIcon, { class: "h-4 w-4" }),
          onClick: () =>
            updateView({ name: _view.name, pinned: !_view.pinned }),
        });
      }
      if (_view?.is_standard && auth.isManager) {
        actions[0].items.push({
          label: _view?.public
            ? __("Hide from sidebar")
            : __("Show in sidebar"),
          icon: h(FeatherIcon, {
            name: _view?.public ? "eye-off" : "eye",
            class: "h-4 w-4",
          }),
          onClick: () =>
            toggleViewVisibility(
              _view,
              __("Hide view from sidebar"),
              __(
                "{0} view is currently visible in the sidebar. Hiding it will remove it from the sidebar.",
                [_view.label]
              )
            ),
        });
      }
      if (!_view.is_standard) {
        if (auth.isManager && !isCustomerPortal.value) {
          actions[0].items.push({
            label: _view?.public ? __("Make Private") : __("Make Public"),
            icon: h(FeatherIcon, {
              name: _view?.public ? "lock" : "unlock",
              class: "h-4 w-4",
            }),
            onClick: () =>
              toggleViewVisibility(
                _view,
                __("Make view private"),
                __(
                  "{0} view is currently public. Changing it to private will hide it for all the users.",
                  [_view.label]
                )
              ),
          });
        }
        actions[0].items.push({
          label: __("Edit"),
          icon: h(EditIcon, { class: "h-4 w-4" }),
          onClick: () => {
            viewDialogConfig.view.label = _view.label;
            viewDialogConfig.view.icon = _view.icon;
            viewDialogConfig.view.name = _view.name;
            viewDialogConfig.mode = "edit";
            viewDialogConfig.show = true;
          },
        });
        actions.push({
          group: __("Delete View"),
          hideLabel: true,
          items: [
            {
              label: __("Delete"),
              icon: "lucide-trash-2",
              theme: "red",
              onClick: () => confirmDeleteView(_view),
            },
          ],
        });
      }
    }
    return actions;
  }

  function confirmDeleteView(_view: View) {
    $dialog({
      title: __("Delete {0}", [_view.label]),
      message:
        __("Are you sure you want to delete this view?") +
        (_view.public
          ? " " + __("This view is public, and will be removed for all users.")
          : ""),
      actions: [
        {
          label: __("Confirm"),
          variant: "solid",
          iconLeft: "trash-2",
          theme: "red",
          onClick({ close }: any) {
            if (route.query.view === _view.name) {
              router.push({
                name: isCustomerPortal.value
                  ? "TicketsCustomer"
                  : "TicketsAgent",
              });
            }
            deleteView(_view.name);
            toast.success(__("View {0}", [__("deleted")]));
            close();
          },
        },
      ],
    });
  }

  function toggleViewVisibility(_view: any, title: string, message: string) {
    const newView: any = { name: _view.name, public: !_view.public };
    if (_view.public) {
      $dialog({
        title,
        message,
        actions: [
          {
            label: __("Confirm"),
            variant: "solid",
            onClick({ close }: any) {
              close();
              updateView(newView);
            },
          },
        ],
      });
    } else {
      updateView(newView);
    }
  }

  // Submit handler for the view modal (create/edit/duplicate). `getList` lets the
  // create flow capture the current list's filters/columns/rows; it is omitted by
  // callers (e.g. the sidebar) that never create a view.
  function handleView(
    viewInfo: any,
    action: string,
    viewDialogConfig: any,
    getList: () => any = () => null
  ) {
    let view: View;
    if (action === "update") {
      updateView({
        name: viewInfo.name,
        label: viewInfo.label,
        icon: viewInfo.icon,
      });
      handleViewSuccess(viewDialogConfig, __("updated"));
      currentView.value = {
        label: viewInfo.label,
        icon: getIcon(viewInfo.icon),
      };
      return;
    } else if (action === "duplicate") {
      const source = findView(viewDialogConfig.view.name).value;
      view = {
        ...source,
        filters: JSON.stringify(source.filters),
        columns: JSON.stringify(source.columns),
        rows: JSON.stringify(source.rows),
        label: viewInfo.label,
        icon: viewInfo.icon,
        public: false,
        pinned: false,
      };
    } else {
      const list = getList();
      view = {
        dt,
        type: "list",
        label: viewInfo.label ?? __("List"),
        icon: viewInfo.icon ?? "",
        route_name: router.currentRoute.value.name as string,
        order_by: list?.params.order_by,
        filters: JSON.stringify(list?.params.filters),
        columns: JSON.stringify(list?.data.columns),
        rows: JSON.stringify(list?.data?.rows),
        pinned: viewInfo.pinned ?? false,
        public: viewInfo.public ?? false,
        is_customer_portal: isCustomerPortal.value,
      };
    }

    createView(view, (d) => {
      currentView.value = {
        label: d.label || __("List"),
        icon: getIcon(d.icon),
      };
      router.push({
        name: isCustomerPortal.value ? "TicketsCustomer" : "TicketsAgent",
        query: { view: d.name },
      });
      handleViewSuccess(viewDialogConfig);
    });
  }

  function handleViewSuccess(
    viewDialogConfig: any,
    msg: string = __("created")
  ) {
    toast.success(__("View {0}", [msg]));
    resetViewDialog(viewDialogConfig);
  }

  function resetViewDialog(viewDialogConfig: any) {
    viewDialogConfig.show = false;
    viewDialogConfig.view.label = "";
    viewDialogConfig.view.icon = "";
    viewDialogConfig.view.name = "";
    viewDialogConfig.mode = null;
  }

  watch(
    () => isCustomerPortal.value,
    (newVal) => {
      views.isCustomerPortal = newVal;
      callGetViews();
    }
  );

  return {
    views,
    getCurrentUserViews,
    pinnedViews,
    publicViews,
    defaultView,
    standardViews,
    findView,
    createView,
    updateView,
    deleteView,
    createOrUpdateDefaultView,
    viewActions,
    handleView,
    resetViewDialog,
  };
}
