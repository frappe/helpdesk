import { computed } from "vue";
import { createResource, createListResource } from "frappe-ui";
import { View } from "@/types";
import { useAuthStore } from "@/stores/auth";

const auth = useAuthStore();

export default function useView(dt: string) {
  const views = createListResource({
    doctype: "HD View",
    fields: ["*"],
    filters: {
      user: auth.userId.value,
      dt,
      type: "list",
    },
    auto: true,
  });

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

  const getPublicViews = computed(() =>
    views.data?.filter((view: View) => view.public).map(parseView)
  );

  function updateView() {}

  function deleteView() {}

  function createOrUpdateDefaultView() {}

  function parseView(view: View) {
    return {
      label: view.label,
      value: view.name,
      icon: view.icon || "align-justify",
    };
  }

  return {
    views,
    getViews,
    getPublicViews,
    findView,
    createView,
    updateView,
    deleteView,
    createOrUpdateDefaultView,
  };
}
