import { createResource } from "frappe-ui";
import { ref } from "vue";

export const holidayListData = createResource({
  url: "frappe.client.get_list",
  params: {
    doctype: "HD Service Holiday List",
    fields: ["*"],
  },
});

export const activeScreen = ref<{
  screen: "list" | "view";
  data: Record<string, any> | null;
}>({ screen: "list", data: null });
