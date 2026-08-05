import { useShortcut } from "@/composables/shortcuts";
import { router } from "@/router";
import { createResource } from "frappe-ui";
import { ref } from "vue";

export const currentTicketIndex = ref(0);

export const ticketsToNavigate = createResource({
  url: "helpdesk.helpdesk.doctype.hd_ticket.api.get_navigation_tickets",
  cache: ["ticketsToNavigate"],
});

// Module scope, not inside the composable: the command palette needs these too,
// and calling the composable a second time would register duplicate shortcuts.

export function goToNextTicket() {
  const nextTicketId = getNextTicket();
  if (!nextTicketId) return null;
  currentTicketIndex.value += 1;
  navigateToTicket(nextTicketId);
  return nextTicketId;
}

export function goToPreviousTicket() {
  const prevTicketId = getPreviousTicket();
  if (!prevTicketId) return null;
  currentTicketIndex.value -= 1;
  navigateToTicket(prevTicketId);
  return prevTicketId;
}

export function getCurrentTicket() {
  return ticketsToNavigate.data[currentTicketIndex.value];
}

export function getNextTicket() {
  if (!ticketsToNavigate.data) return null;
  if (currentTicketIndex.value < ticketsToNavigate.data.length - 1) {
    return ticketsToNavigate.data[currentTicketIndex.value + 1];
  }
  return null;
}

export function getPreviousTicket() {
  if (!ticketsToNavigate.data) return null;
  if (currentTicketIndex.value > 0) {
    return ticketsToNavigate.data[currentTicketIndex.value - 1];
  }
  return null;
}

export function navigateToTicket(ticketId: string) {
  const view = router.currentRoute.value.query.view as string;
  const routeToNavigate: any = {
    name: "TicketAgent",
    params: { ticketId },
    hash: "",
  };
  if (view) {
    routeToNavigate["query"] = { view };
  }
  router.push(routeToNavigate);
}

/** True once the view has more than one ticket to move between. */
export function canNavigateTickets() {
  return !ticketsToNavigate.loading && ticketsToNavigate.data?.length > 1;
}

/**
 * Shift + < / > to move through the current view's tickets. Listeners are
 * registered per caller, so call this once per page (the ticket page).
 */
export function useTicketNavigation() {
  useShortcut(
    { key: ">", shift: true },
    () => canNavigateTickets() && goToNextTicket()
  );
  useShortcut(
    { key: "<", shift: true },
    () => canNavigateTickets() && goToPreviousTicket()
  );
}
