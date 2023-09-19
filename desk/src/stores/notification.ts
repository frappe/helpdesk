import { ref } from "vue";
import { defineStore } from "pinia";
import { createListResource } from "frappe-ui";

export const useNotificationStore = defineStore("notification", () => {
  const visible = ref(false);
  const resource = createListResource({
    doctype: "HD Notification",
    cache: "Notifications",
    orderBy: "creation asc",
    auto: true,
    initialValue: [],
  });

  function toggle() {
    visible.value = !visible.value;
  }

  return {
    data: resource.data,
    toggle,
    visible,
  };
});
