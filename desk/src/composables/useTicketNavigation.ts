import { createResource } from "frappe-ui";
import { ref } from "vue";
import { useRouter } from "vue-router";

export const currentTicketIndex = ref(0);

export const ticketsToNavigate = createResource({
  url: "helpdesk.helpdesk.doctype.hd_ticket.api.get_open_tickets",
  cache: ["ticketsToNavigate"],
});

export function useTicketNavigation() {
  const router = useRouter();

  function goToNextTicket() {
    if (currentTicketIndex.value < ticketsToNavigate.data.length - 1) {
      currentTicketIndex.value += 1;
      const nextTicketId = ticketsToNavigate.data[currentTicketIndex.value];
      navigateToTicket(nextTicketId);
      return nextTicketId;
    }
    return null;
  }

  function goToPreviousTicket() {
    if (currentTicketIndex.value > 0) {
      currentTicketIndex.value -= 1;
      const prevTicketId = ticketsToNavigate.data[currentTicketIndex.value];
      navigateToTicket(prevTicketId);
      return prevTicketId;
    }
    return null;
  }

  function getCurrentTicket() {
    return ticketsToNavigate.data[currentTicketIndex.value];
  }

  function navigateToTicket(ticketId: string) {
    router.push({
      name: "TicketAgent2",
      params: { ticketId },
    });
  }

  // Remove the watcher that was causing conflicts

  return {
    currentTicketIndex,
    ticketsToNavigate,
    goToNextTicket,
    goToPreviousTicket,
    getCurrentTicket,
    navigateToTicket,
  };
}
