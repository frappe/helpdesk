import { useAuthStore } from "@/stores/auth";
import { globalStore } from "@/stores/globalStore";
import { toast } from "frappe-ui";
import { ref } from "vue";

export function useActiveViewers(ticketId: string) {
  const { $socket } = globalStore();
  const currentViewers = ref<string[]>([]);
  const { userId } = useAuthStore();
  $socket.on("ticket_viewers", (data: { ticket_id: string; users: string }) => {
    if (data.ticket_id === ticketId) {
      const viewers = JSON.parse(data.users).filter(
        (u: string) => u !== userId
      );
      currentViewers.value = viewers.length ? viewers : [];
    }
  });

  const handleBeforeUnload = () => {
    $socket.emit("stop_view_ticket", ticketId);
  };
  const startViewing = () => {
    $socket.emit("view_ticket", ticketId);
    window.addEventListener("beforeunload", handleBeforeUnload);
  };
  const stopViewing = () => {
    $socket.emit("stop_view_ticket", ticketId);
    window.removeEventListener("beforeunload", handleBeforeUnload);
  };

  return {
    currentViewers,
    startViewing,
    stopViewing,
  };
}

export function useNotifyTicketUpdate(ticketId: string) {
  const { $socket } = globalStore();
  const notifyTicketUpdate = (field: string, value: string) => {
    $socket.emit("notify_ticket_update", ticketId, field, value);
  };
  $socket.on(
    "ticket_update",
    (data: {
      ticket_id: string;
      user: string;
      field: string;
      value: string;
    }) => {
      if (data.ticket_id === ticketId) {
        // Notify the user about the update
        toast.info(`User ${data.user} updated ${data.field} to ${data.value}`);
      }
    }
  );
  return { notifyTicketUpdate };
}
