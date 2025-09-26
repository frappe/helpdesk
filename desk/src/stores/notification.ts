import { useAuthStore } from "@/stores/auth";
import { Notification, Resource } from "@/types";
import { createListResource, createResource } from "frappe-ui";
import { defineStore } from "pinia";
import { computed, ref, watch } from "vue";

export const useNotificationStore = defineStore("notification", () => {
  const authStore = useAuthStore();

  const visible = ref(false);
  const resource: Resource<Array<Notification>> = createListResource({
    doctype: "HD Notification",
    cache: "Notifications",
    fields: [
      "creation",
      "name",
      "notification_type",
      "read",
      "reference_comment",
      "reference_ticket",
      "user_from",
      "user_to",
    ],
    orderBy: "creation desc",
  });
  const clear = createResource({
    url: "helpdesk.helpdesk.doctype.hd_notification.utils.clear",
    auto: false,
    onSuccess: () => resource.reload(),
  });

  const read = (ticket) => {
    createResource({
      url: "helpdesk.helpdesk.doctype.hd_notification.utils.clear",
      auto: true,
      params: {
        ticket: ticket,
      },
      onSuccess: () => resource.reload(),
    });
  };

  const data = computed(() => resource.data || []);
  const unread = computed(() => data.value.filter((d) => !d.read).length);

  function toggle() {
    visible.value = !visible.value;
  }

  watch(
    () => authStore.hasDeskAccess,
    (newVal) => {
      if (!newVal) return;
      resource.filters = {
        user_to: ["=", authStore.userId],
      };
      resource.reload();
    },
    { immediate: true }
  );

  return {
    clear,
    data,
    toggle,
    read,
    unread,
    visible,
    resource,
  };
});
