import { useAuthStore } from "@/stores/auth";
import { View } from "@/types";
import { getIcon, isCustomerPortal } from "@/utils";
import { useDebounceFn } from "@vueuse/core";
import { call, createListResource, createResource } from "frappe-ui";
import { computed, ref, watch } from "vue";
import { useRouter } from "vue-router";

const debouncedSetValue = useDebounceFn(
  (doctype: string, name: string, fieldname: any, cb?: Function) => {
    call("frappe.client.set_value", { doctype, name, fieldname }).then(() => {
      cb?.();
      views.reload();
    });
  },
  500
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
  };
}
