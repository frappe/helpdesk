import { computed, ref } from "vue";
import { defineStore } from "pinia";
import { createListResource } from "frappe-ui";
import { Notification, Resource } from "@/types";

export const useNotificationStore = defineStore("notification", () => {
  const visible = ref(true);
  const resource: Resource<Array<Notification>> = createListResource({
    doctype: "HD Notification",
    // cache: "Notifications",
    fields: [
      "creation",
      "name",
      "notification_type",
      "reference_comment",
      "reference_ticket",
      "user_from",
      "user_to",
    ],
    orderBy: "creation asc",
    auto: true,
    initialValue: [],
  });
  const data = computed(() => resource.data);
  const unread = computed(() => data.value.filter((d) => !d.read).length);

  function toggle() {
    visible.value = !visible.value;
  }

  return {
    data,
    toggle,
    unread,
    visible,
  };
});
