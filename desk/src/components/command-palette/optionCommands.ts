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
  /** "<prefix>: <value>" for root rows, where a bare "Urgent" is ambiguous. */
  titlePrefix?: string | undefined;
  hideWhenEmpty?: boolean | undefined;
  weight?: number | undefined;
}

/** Shared by "Set status" and "Filter by status" — same options, different verb. */
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

/** Live option names as parent keywords — site-defined values a hardcoded list
 * would miss. Empty until the store resolves; the title still matches. */
export function statusKeywords(): string {
  return (useTicketStatusStore().statuses.data ?? [])
    .filter((status) => status.enabled)
    .map((status) => status.label_agent)
    .join(" ");
}

export function priorityKeywords(): string {
  return (useTicketPriorityStore().priorities.data ?? [])
    .filter((priority) => !priority.disabled)
    .map((priority) => priority.name)
    .join(" ");
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
