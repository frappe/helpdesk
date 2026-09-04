import { views } from "@/composables/useView";
import { useAuthStore } from "@/stores/auth";
import { useConfigStore } from "@/stores/config";
import { globalStore } from "@/stores/globalStore";
import { __ } from "@/translation";
import { isCustomerPortal } from "@/utils";
import { ref } from "vue";
import { useRouter } from "vue-router";

type PushPayload = {
  notification_type: "Assignment" | "Mention" | "Reaction";
  user_from: string;
  reference_ticket?: string;
};

const isSupported = typeof window !== "undefined" && "Notification" in window;
const permission = ref<NotificationPermission>(
  isSupported ? Notification.permission : "denied"
);

// Module-level guard so the socket handler is registered only once.
let listening = false;

export function usePushNotifications() {
  const router = useRouter();
  const auth = useAuthStore();
  const { $socket } = globalStore();
  const configStore = useConfigStore();

  function enable() {
    if (!isSupported) return;
    Notification.requestPermission().then((result) => {
      permission.value = result;
    });
  }

  function show(payload: PushPayload) {
    if (permission.value !== "granted" || isCustomerPortal.value) return;
    // Assignment/reopen land in the agent's "my open tickets" list, so skip the
    // popup while they're already looking at such a view. Mentions always fire.
    if (payload.notification_type !== "Mention" && onMyOpenTicketsView()) return;

    const notification = new Notification(getTitle(payload), {
      body: payload.reference_ticket
        ? `${__("Ticket")} #${payload.reference_ticket}`
        : "",
      icon: configStore.favicon,
      // tag collapses repeats for the same ticket; omit it when absent
      // (exactOptionalPropertyTypes disallows an explicit undefined).
      ...(payload.reference_ticket ? { tag: payload.reference_ticket } : {}),
    });

    notification.onclick = () => {
      window.focus();
      notification.close();
      if (payload.reference_ticket) {
        router.push({
          name: "TicketAgent",
          params: { ticketId: payload.reference_ticket },
        });
      }
    };
  }

  // True when the current route is a HD Ticket list whose active view already
  // surfaces the agent's freshly assigned/reopened tickets (assignee = me + open).
  function onMyOpenTicketsView(): boolean {
    const route = router.currentRoute.value;
    if (route.name !== "TicketsAgent") return false;

    const viewName = route.query.view as string | undefined;
    const view = viewName
      ? views.data?.find((v: any) => v.name === viewName)
      : views.data?.find(
          (v: any) =>
            v.is_default && v.user === auth.userId && v.dt === "HD Ticket"
        );

    const filters = view?.filters;
    return !!filters && assignedToMe(filters) && showsOpen(filters);
  }

  function assignedToMe(filters: Record<string, any>): boolean {
    if (!filters._assign) return false;
    const value = JSON.stringify(filters._assign);
    return value.includes("@me") || value.includes(auth.userId);
  }

  function showsOpen(filters: Record<string, any>): boolean {
    // Require an explicit open-status filter. Without one, another filter
    // (e.g. the "My Feedback" view needs feedback set) can still hide a freshly
    // assigned open ticket, so we must not assume the view shows it.
    const status = filters.status_category ?? filters.status;
    return status != null && JSON.stringify(status).includes("Open");
  }

  if (isSupported && !listening) {
    listening = true;
    $socket.on("helpdesk:new-notification", show);
  }

  return { isSupported, permission, enable };
}

function getTitle(payload: PushPayload): string {
  switch (payload.notification_type) {
    case "Mention":
      return `${payload.user_from} ${__("mentioned you in a ticket")}`;
    case "Assignment":
      return `${payload.user_from} ${__("assigned you a ticket")}`;
    case "Reaction":
      return `${payload.user_from} ${__("reopened a ticket")}`;
    default:
      return __("New notification");
  }
}
