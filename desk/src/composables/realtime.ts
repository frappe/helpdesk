import { useAuthStore } from "@/stores/auth";
import { globalStore } from "@/stores/globalStore";
import { reactive } from "vue";

const currentViewers = reactive<Record<string, string[]> | null>({});

export function useActiveViewers(ticketId: string) {
  const { $socket } = globalStore();

  const { userId } = useAuthStore();
  $socket.on("ticket_viewers", (data: { ticket_id: string; users: string }) => {
    if (data.ticket_id === ticketId) {
      const viewers = JSON.parse(data.users).filter(
        (u: string) => u !== userId
      );
      currentViewers[ticketId] = viewers;
    }
  });

  const handleBeforeUnload = (_ticketId: string) => {
    $socket.emit("stop_view_ticket", _ticketId);
  };
  const startViewing = (_ticketId: string) => {
    $socket.emit("view_ticket", _ticketId);
    window.addEventListener("beforeunload", () =>
      handleBeforeUnload(_ticketId)
    );
  };

  const stopViewing = (_ticketId: string) => {
    $socket.emit("stop_view_ticket", _ticketId);

    window.removeEventListener("beforeunload", () =>
      handleBeforeUnload(_ticketId)
    );
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
  // how to check if $socket is already listening to avoid multiple listeners
  return { notifyTicketUpdate };
}
