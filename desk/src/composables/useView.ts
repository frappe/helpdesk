import { computed, ref, watch } from "vue";
import { createResource, createListResource, call } from "frappe-ui";
import { View } from "@/types";
import { useAuthStore } from "@/stores/auth";
import { useRouter } from "vue-router";
import { getIcon } from "@/utils";
import { isCustomerPortal } from "@/utils";

const auth = useAuthStore();

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
});

export const currentView = ref({
  label: "List",
  icon: "lucide:align-justify",
});

export function useView(dt: string = null) {
  const router = useRouter();

  function callGetViews() {
    if (
      (views.filters?.dt === dt && views.data?.length > 0) ||
      views.list?.promise ||
      views.isCustomerPortal === isCustomerPortal.value
    ) {
      return;
    }

    const filters = {
      dt,
      is_customer_portal: isCustomerPortal.value,
    };
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
          !view.pinned
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
          user: auth.userId,
          ...view,
        },
      },
      auto: true,
      onSuccess: (d) => {
        console.log("success");
        views.reload();
        successCB(d);
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

  function updateView(view: View, successCB: Function = () => {}) {
    if (view.name) {
      // handle custom view
      console.log("custom");
      call("frappe.client.set_value", {
        doctype: "HD View",
        name: view.name,
        fieldname: view,
      }).then(() => {
        successCB();
      });
    } else {
      // handle default view
      console.log("default");
    }
  }

  function deleteView() {}

  function createOrUpdateDefaultView() {}

  function parseView(view: View) {
    return {
      label: view.label,
      value: view.name,
      icon: getIcon(view.icon),
      route_name: view.route_name,
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
    findView,
    createView,
    updateView,
    deleteView,
    createOrUpdateDefaultView,
  };
}
