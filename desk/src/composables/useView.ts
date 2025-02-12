import { ref, computed, watch } from "vue";
import { useRoute } from "vue-router";
import { createResource, createListResource } from "frappe-ui";
import { View } from "@/types";
import { useAuthStore } from "@/stores/auth";
const auth = useAuthStore();

export default function useView(dt: string) {
  const views = createListResource({
    doctype: "HD View",
    fields: ["*"],
    cache: [`HD View-${dt}`],
    filters: {
      user: auth.userId.value,
      dt,
      type: "list",
    },
  });

  async function getViews() {
    if (views.data.length === 0 && !views.loading) {
      await views.fetch();
    }
    return views.data;
  }

  async function createView(
    view: View,
    successCB: Function = () => {},
    errorCB: Function = () => {}
  ) {
    // return;

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

  function updateView() {}

  function deleteView() {}

  function createOrUpdateDefaultView() {}

  return {
    views,
    getViews,
    createView,
    updateView,
    deleteView,
    createOrUpdateDefaultView,
  };
}
