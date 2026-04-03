import { useAuthStore } from "@/stores/auth";
import { globalStore } from "@/stores/globalStore";
import { reactive, ref, watch } from "vue";

const currentViewers = reactive<Record<string, string[]>>({});

export function useActiveViewers(ticketId: string) {
  const { $socket } = globalStore();

  const { userId } = useAuthStore();

  const onTicketViewers = (data: { ticket_id: string; users: string }) => {
    if (data.ticket_id === ticketId) {
      try {
        const viewers = JSON.parse(data.users).filter(
          (u: string) => u !== userId
        );
        currentViewers[ticketId] = viewers;
      } catch {
        currentViewers[ticketId] = [];
      }
    }
  };

  $socket.on("ticket_viewers", onTicketViewers);

  const beforeUnloadHandler = () => {
    $socket.emit("stop_view_ticket", ticketId);
  };

  const startViewing = (_ticketId: string) => {
    $socket.emit("view_ticket", _ticketId);
    window.addEventListener("beforeunload", beforeUnloadHandler);
  };

  const stopViewing = (_ticketId: string) => {
    $socket.emit("stop_view_ticket", _ticketId);
    window.removeEventListener("beforeunload", beforeUnloadHandler);
    delete currentViewers[_ticketId];
  };

  const cleanup = () => {
    $socket.off("ticket_viewers", onTicketViewers);
    window.removeEventListener("beforeunload", beforeUnloadHandler);
    delete currentViewers[ticketId];
  };

  return {
    currentViewers,
    startViewing,
    stopViewing,
    cleanup,
  };
}

export function useNotifyTicketUpdate(ticketId: string) {
  const { $socket } = globalStore();
  const notifyTicketUpdate = (field: string, value: string) => {
    $socket.emit("notify_ticket_update", ticketId, field, value);
  };
  return { notifyTicketUpdate };
}

export function useTyping(ticketId: string) {
  const { $socket } = globalStore();
  const { userId } = useAuthStore();

  const typingCounter = ref(0);
  const isTyping = ref(false);
  const typingUsers = reactive<string[]>([]);
  let timeout: any = null;

  const onTyping = (data: { ticket_id: string; user: string }) => {
    if (data.ticket_id === ticketId && data.user !== userId) {
      if (!typingUsers.includes(data.user)) {
        typingUsers.push(data.user);
      }
    }
  };

  const onTypingStopped = (data: { ticket_id: string; user: string }) => {
    if (data.ticket_id === ticketId) {
      const index = typingUsers.indexOf(data.user);
      if (index > -1) {
        typingUsers.splice(index, 1);
      }
    }
  };

  // Listen for typing events from other users
  $socket.on("helpdesk_ticket_typing", onTyping);
  $socket.on("helpdesk_ticket_typing_stopped", onTypingStopped);

  const emitStartTyping = () => {
    $socket?.emit("helpdesk_ticket_typing", ticketId);
  };

  const emitStopTyping = () => {
    $socket?.emit("helpdesk_ticket_typing_stopped", ticketId);
  };

  const onUserType = () => {
    if (!isTyping.value) {
      isTyping.value = true;
      typingCounter.value = typingCounter.value + 1;
      emitStartTyping();
    }
  };

  // Reset the typing state after 10 seconds of inactivity
  watch(typingCounter, (newVal) => {
    if (timeout) {
      clearTimeout(timeout);
    }

    if (newVal > 0) {
      timeout = setTimeout(() => {
        isTyping.value = false;
        typingCounter.value = 0;
        emitStopTyping();
      }, 10000);
    }
  });

  const stopTyping = () => {
    emitStopTyping();
    isTyping.value = false;
    typingCounter.value = 0;
    if (timeout) {
      clearTimeout(timeout);
    }
  };

  const cleanup = () => {
    stopTyping();
    if (timeout) {
      clearTimeout(timeout);
    }
    // Remove specific socket listeners to avoid removing others
    $socket.off("helpdesk_ticket_typing", onTyping);
    $socket.off("helpdesk_ticket_typing_stopped", onTypingStopped);
  };

  return {
    stopTyping,
    onUserType,
    typingUsers,
    cleanup,
  };
}
