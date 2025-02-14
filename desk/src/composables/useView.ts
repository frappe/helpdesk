import { computed } from "vue";
import { createResource, createListResource, call } from "frappe-ui";
import { View } from "@/types";
import { useAuthStore } from "@/stores/auth";
import { useRouter } from "vue-router";
import { getIcon } from "@/utils";

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

export function useView(dt: string = null) {
  const router = useRouter();

  function callGetViews() {
    if (
      (views.filters?.dt === dt && views.data?.length > 0) ||
      views.list?.promise
    ) {
      return;
    }
    views.update({
      filters: {
        dt,
        type: "list",
        user: auth.userId,
      },
    });
    views.fetch();
  }
  callGetViews();

  const getViews = computed(() =>
    views.data?.filter((view: View) => !view.is_default).map(parseView)
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
    views.data?.filter((view: View) => view.pinned).map(parseView)
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

  return {
    views,
    getViews,
    pinnedViews,
    findView,
    createView,
    updateView,
    deleteView,
    createOrUpdateDefaultView,
  };
}
