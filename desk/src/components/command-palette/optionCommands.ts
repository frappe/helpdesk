import TicketPriority from "@/components/TicketPriority.vue";
import { useTicketPriorityStore } from "@/stores/ticketPriority";
import { useTicketStatusStore } from "@/stores/ticketStatus";
import { __ } from "@/translation";
import type { Command } from "./paletteTypes";

/**
 * Shared by the ticket context ("Set status") and the list context ("Filter by
 * status") — same options, different verb. Ids need only be unique per level.
 */
export function statusOptions(
  group: string,
  onPick: (status: string) => void
): Command[] {
  const statuses = useTicketStatusStore().statuses.data ?? [];
  return statuses
    .filter((status) => status.enabled)
    .map((status) => ({
      id: `status-${status.label_agent}`,
      title: __(status.label_agent),
      group,
      dotClass: status.parsed_color,
      perform: () => onPick(status.label_agent),
    }));
}

export function priorityOptions(
  group: string,
  onPick: (priority: string) => void
): Command[] {
  const priorities = useTicketPriorityStore().priorities.data ?? [];
  return priorities
    .filter((priority) => !priority.disabled)
    .map((priority) => ({
      id: `priority-${priority.name}`,
      title: __(priority.name),
      group,
      // The app's own level-aware icon, not a flat flag for every priority.
      icon: TicketPriority,
      iconProps: { priority: priority.name, iconOnly: true },
      perform: () => onPick(priority.name),
    }));
}
