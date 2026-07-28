import TicketPriority from "@/components/TicketPriority.vue";
import { useTicketPriorityStore } from "@/stores/ticketPriority";
import { useTicketStatusStore } from "@/stores/ticketStatus";
import { __ } from "@/translation";
import type { Command } from "./paletteTypes";

interface OptionListConfig {
  /** Group heading, and the verb the rows read as: "Set status", "Filter by status". */
  group: string;
  onPick: (value: string) => void;
  /** Ticks the row already in effect. */
  current?: string | undefined;
  /**
   * Composes the title as "<prefix>: <value>" for rows that live at the root
   * level, where a bare "Urgent" reads as a ticket, a filter or a status.
   */
  titlePrefix?: string | undefined;
  hideWhenEmpty?: boolean | undefined;
  weight?: number | undefined;
}

/**
 * Shared by the ticket context ("Set status") and the list context ("Filter by
 * status") — same options, different verb. Ids need only be unique per level.
 */
export function statusOptions(config: OptionListConfig): Command[] {
  const statuses = useTicketStatusStore().statuses.data ?? [];
  return statuses
    .filter((status) => status.enabled)
    .map((status) => ({
      ...optionRow(config, status.label_agent),
      id: `status-${status.label_agent}`,
      dotClass: status.parsed_color,
    }));
}

export function priorityOptions(config: OptionListConfig): Command[] {
  const priorities = useTicketPriorityStore().priorities.data ?? [];
  return priorities
    .filter((priority) => !priority.disabled)
    .map((priority) => ({
      ...optionRow(config, priority.name),
      id: `priority-${priority.name}`,
      // The app's own level-aware icon, not a flat flag for every priority.
      icon: TicketPriority,
      iconProps: { priority: priority.name, iconOnly: true },
    }));
}

function optionRow(config: OptionListConfig, value: string): Command {
  const label = __(value);
  return {
    id: value,
    title: config.titlePrefix ? `${__(config.titlePrefix)}: ${label}` : label,
    group: config.group,
    checked: value === config.current,
    perform: () => config.onPick(value),
    ...(config.hideWhenEmpty ? { hideWhenEmpty: true } : {}),
    ...(config.weight ? { weight: config.weight } : {}),
    // Matches "urgent" typed on its own, not just the composed title.
    ...(config.titlePrefix ? { keywords: value } : {}),
  };
}
