import { router } from "@/router";
import { useAuthStore } from "@/stores/auth";
import { __ } from "@/translation";
import { htmlToText } from "@/utils";
import { useWebNotification } from "@vueuse/core";
import { createListResource } from "frappe-ui";
import { defineStore } from "pinia";
import { ref, watch } from "vue";
import { globalStore } from "./globalStore";

type NewTicketLog = {
  name: string;
  title: string;
  description: string;
  document_name: string;
};

// a popup's tag is its ticket, except for the one grouping several tickets
const GROUPED_TAG = "helpdesk-new-tickets";

/** Desktop popups for the session user's "New Ticket" notifications. */
export const useDesktopNotificationStore = defineStore(
  "desktopNotification",
  () => {
    const authStore = useAuthStore();
    const { $socket } = globalStore();
    const { isSupported, ensurePermissions, show, onClick } =
      useWebNotification({ requestPermissions: false });
    const permission = ref<NotificationPermission>(
      isSupported.value ? Notification.permission : "denied"
    );

    // rows already shown, plus the backlog the first fetch finds
    const shown = new Set<string>();
    let primed = false;
    const unreadNewTickets = createListResource({
      doctype: "Notification Log",
      fields: ["name", "title", "description", "document_name"],
      filters: { for_user: authStore.userId, type: "New Ticket", read: 0 },
      orderBy: "creation desc",
      pageLength: 20,
      onSuccess(rows: NewTicketLog[]) {
        const fresh = rows.filter((row) => !shown.has(row.name));
        fresh.forEach((row) => shown.add(row.name));
        if (primed) showPopups(fresh);
        primed = true;
      },
    });
    // nothing to fetch until popups are allowed; the first fetch primes
    watch(
      permission,
      (value) => {
        if (value === "granted") unreadNewTickets.reload();
      },
      { immediate: true }
    );
    $socket.on("notification", () => {
      if (permission.value === "granted") unreadNewTickets.reload();
    });

    function showPopups(rows: NewTicketLog[]) {
      if (!rows.length) return;
      if (rows.length > 1) {
        show({
          title: __("{0} new tickets", [rows.length]),
          tag: GROUPED_TAG,
        });
        return;
      }
      show({
        title: htmlToText(rows[0].title),
        body: htmlToText(rows[0].description),
        // one popup per ticket, however many tabs are open
        tag: rows[0].document_name,
      });
    }

    onClick((event: Event) => {
      const popup = event.target as Notification;
      window.focus();
      router.push(
        popup.tag === GROUPED_TAG
          ? { name: "TicketsAgent" }
          : { name: "TicketAgent", params: { ticketId: popup.tag } }
      );
      popup.close();
    });

    // must run from a click: browsers ignore permission prompts without one
    async function enable() {
      await ensurePermissions();
      permission.value = Notification.permission;
    }

    return { enable, isSupported, permission };
  }
);
