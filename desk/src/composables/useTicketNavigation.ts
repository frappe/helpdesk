import { createResource } from "frappe-ui";
import { ref } from "vue";
import { useRoute, useRouter } from "vue-router";

export const currentTicketIndex = ref(0);

export const ticketsToNavigate = createResource({
  url: "helpdesk.helpdesk.doctype.hd_ticket.api.get_navigation_tickets",
  cache: ["ticketsToNavigate"],
});

export function useTicketNavigation() {
  const router = useRouter();
  const route = useRoute();

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

  function getNextTicket() {
    if (!ticketsToNavigate.data) return null;
    if (currentTicketIndex.value < ticketsToNavigate.data.length - 1) {
      return ticketsToNavigate.data[currentTicketIndex.value + 1];
    }
    return null;
  }

  function getPreviousTicket() {
    if (!ticketsToNavigate.data) return null;
    if (currentTicketIndex.value > 0) {
      return ticketsToNavigate.data[currentTicketIndex.value - 1];
    }
    return null;
  }

  function navigateToTicket(ticketId: string) {
    let view = route.query.view as string;
    let routeToNavigate: any = {
      name: "TicketAgent",
      params: { ticketId },
    };
    if (view) {
      routeToNavigate["query"] = { view };
    }
    router.push(routeToNavigate);
  }

  // Remove the watcher that was causing conflicts

  return {
    currentTicketIndex,
    ticketsToNavigate,
    goToNextTicket,
    goToPreviousTicket,
    getCurrentTicket,
    getNextTicket,
    getPreviousTicket,
    navigateToTicket,
  };
}
