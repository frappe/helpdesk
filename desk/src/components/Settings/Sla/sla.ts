import { ref } from "vue";
import { createResource } from "frappe-ui";

export const slaPolicyListData = createResource({
  url: "frappe.client.get_list",
  params: {
    doctype: "HD Service Level Agreement",
    fields: ["*"],
  },
});

export const activeScreen = ref<{
  screen: "list" | "view";
  data: Record<string, any> | null;
}>({ screen: "list", data: null });
