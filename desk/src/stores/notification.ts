import { useAuthStore } from "@/stores/auth";
import { NotificationLog, useNotifications } from "@framework/ui";
import { defineStore } from "pinia";
import { computed, ref, watch } from "vue";
import { RouteLocationRaw } from "vue-router";
import { globalStore } from "./globalStore";

export const useNotificationStore = defineStore("notification", () => {
  const authStore = useAuthStore();
  const { $socket } = globalStore();

  const visible = ref(false);
  const controller = useNotifications({
    appName: "helpdesk",
    currentUser: authStore.userId,
    socket: $socket,
  });

  const unread = computed(() => controller.unreadCount);

  const readFilter = ref<"all" | "unread">("all");
  // a Notification Log `type`; empty for all categories
  const category = ref("");

  function toggle() {
    visible.value = !visible.value;
    if (visible.value) controller.markSeen();
    else resetFilters();
  }

  // the filters also scope the bell's unread count, so drop them on leaving
  function resetFilters() {
    readFilter.value = "all";
    category.value = "";
  }

  // Every helpdesk notification references the ticket; the ones about a
  // comment carry it as the source, which is the deep-link target.
  function routeFor(n: NotificationLog): RouteLocationRaw | null {
    if (n.document_type !== "HD Ticket" || !n.document_name) return null;
    const route = {
      name: "TicketAgent",
      params: { ticketId: n.document_name },
    };
    if (n.source_doctype !== "Comment" || !n.source_name) return route;
    return {
      ...route,
      // ?highlight is the activity deep-link target (element id); the hash
      // only selects the tab
      hash: "#activity",
      query: { highlight: "comment-" + n.source_name },
    };
  }

  watch([readFilter, category], () => {
    const filters: Record<string, unknown> = {};
    if (readFilter.value === "unread") filters.read = 0;
    if (category.value) filters.type = category.value;
    controller.setFilters(filters);
  });

  return {
    category,
    controller,
    toggle,
    routeFor,
    unread,
    readFilter,
    resetFilters,
    visible,
  };
});
