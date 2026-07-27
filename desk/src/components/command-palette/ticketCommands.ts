import { useTicket } from "@/composables/useTicket";
import {
  canNavigateTickets,
  getNextTicket,
  getPreviousTicket,
  goToNextTicket,
  goToPreviousTicket,
} from "@/composables/useTicketNavigation";
import {
  showMergeModal,
  toggleCommentBox,
  toggleEmailBox,
} from "@/pages/ticket/modalStates";
import { useAgentStore } from "@/stores/agent";
import { __ } from "@/translation";
import { copyToClipboard } from "@/utils";
import { createListResource, createResource, toast } from "frappe-ui";
import { priorityOptions, statusOptions } from "./optionCommands";
import { tagChildren } from "./tagCommands";
import { CONTEXT_WEIGHT, GROUP, type Command } from "./paletteTypes";

import LucideArrowLeft from "~icons/lucide/arrow-left";
import LucideArrowRight from "~icons/lucide/arrow-right";
import LucideCircleDot from "~icons/lucide/circle-dot";
import LucideCopy from "~icons/lucide/copy";
import LucideCornerUpLeft from "~icons/lucide/corner-up-left";
import LucideFlag from "~icons/lucide/flag";
import LucideLink from "~icons/lucide/link";
import LucideMerge from "~icons/lucide/merge";
import LucideMessageCircle from "~icons/lucide/message-circle";
import LucideTag from "~icons/lucide/tag";
import LucideTags from "~icons/lucide/tags";
import LucideUserPlus from "~icons/lucide/user-plus";
import LucideUsers from "~icons/lucide/users";

// --- ticket context ------------------------------------------------------

/**
 * Actions on the ticket you're looking at. `weight` keeps them above server
 * search hits, which carry a fixed rank — context should win on purpose, not
 * by a few points of fuzzy-score luck.
 */
export function ticketCommands(ticketId: string): Command[] {
  const commands: Command[] = [
    {
      id: "ticket-status",
      title: __("Change status"),
      group: GROUP.ticket,
      weight: CONTEXT_WEIGHT,
      icon: LucideCircleDot,
      hint: "S",
      keywords: "state open closed paused resolved",
      children: () => statusChildren(ticketId),
    },
    {
      id: "ticket-priority",
      title: __("Change priority"),
      group: GROUP.ticket,
      weight: CONTEXT_WEIGHT,
      icon: LucideFlag,
      hint: "P",
      keywords: "urgent high medium low",
      children: () => priorityChildren(ticketId),
    },
    {
      id: "ticket-assign",
      title: __("Assign to"),
      group: GROUP.ticket,
      weight: CONTEXT_WEIGHT,
      icon: LucideUserPlus,
      hint: "A",
      keywords: "agent owner assignee",
      children: () => agentChildren(ticketId),
    },
    {
      id: "ticket-team",
      title: __("Change team"),
      group: GROUP.ticket,
      weight: CONTEXT_WEIGHT,
      icon: LucideUsers,
      hint: "Shift+T",
      keywords: "group agent_group",
      children: () => teamChildren(ticketId),
    },
    {
      id: "ticket-type",
      title: __("Change type"),
      group: GROUP.ticket,
      weight: CONTEXT_WEIGHT,
      icon: LucideTag,
      hint: "T",
      keywords: "question incident bug",
      children: () => ticketTypeChildren(ticketId),
    },
    {
      id: "ticket-reply",
      title: __("Reply to ticket"),
      group: GROUP.ticket,
      weight: CONTEXT_WEIGHT,
      icon: LucideCornerUpLeft,
      hint: "R",
      keywords: "email respond",
      perform: () => toggleEmailBox(),
    },
    {
      id: "ticket-comment",
      title: __("Add comment"),
      group: GROUP.ticket,
      weight: CONTEXT_WEIGHT,
      icon: LucideMessageCircle,
      hint: "C",
      keywords: "note internal",
      perform: () => toggleCommentBox(),
    },
    {
      id: "ticket-tags",
      title: __("Add tag"),
      group: GROUP.ticket,
      weight: CONTEXT_WEIGHT,
      icon: LucideTags,
      hint: "G",
      keywords: "label categorise",
      children: () => tagChildren(ticketId),
    },
    ...mergeCommand(ticketId),
    ...navigationCommands(),
    {
      id: "ticket-copy-id",
      title: __("Copy ticket ID"),
      group: GROUP.ticket,
      weight: CONTEXT_WEIGHT,
      icon: LucideCopy,
      hint: "Mod+.",
      perform: () =>
        copyToClipboard(ticketId, __("Ticket #{0} copied", [ticketId])),
    },
    {
      id: "ticket-copy-url",
      title: __("Copy ticket link"),
      group: GROUP.ticket,
      weight: CONTEXT_WEIGHT,
      icon: LucideLink,
      hint: "Mod+Shift+.",
      perform: () =>
        copyToClipboard(window.location.href, __("Ticket URL copied")),
    },
  ];

  return commands;
}

/**
 * Same guards as the ticket header's own Merge action: an already-merged or
 * resolved ticket has nothing to merge into.
 */
function mergeCommand(ticketId: string): Command[] {
  const doc = useTicket(ticketId).ticket.doc;
  const mergeable =
    doc && !doc.is_merged && ["Open", "Paused"].includes(doc.status_category);
  if (!mergeable) return [];
  return [
    {
      id: "ticket-merge",
      title: __("Merge ticket"),
      group: GROUP.ticket,
      weight: CONTEXT_WEIGHT,
      icon: LucideMerge,
      keywords: "combine duplicate join",
      perform: () => (showMergeModal.value = true),
    },
  ];
}

/** Only offered when there's somewhere to go, so the rows never no-op. */
function navigationCommands(): Command[] {
  if (!canNavigateTickets()) return [];
  const commands: Command[] = [];
  const next = getNextTicket();
  const previous = getPreviousTicket();
  if (next) {
    commands.push({
      id: "ticket-next",
      title: __("Next ticket"),
      subtitle: `#${next}`,
      group: GROUP.ticket,
      weight: CONTEXT_WEIGHT,
      icon: LucideArrowRight,
      hint: "Shift+>",
      perform: () => goToNextTicket(),
    });
  }
  if (previous) {
    commands.push({
      id: "ticket-previous",
      title: __("Previous ticket"),
      subtitle: `#${previous}`,
      group: GROUP.ticket,
      weight: CONTEXT_WEIGHT,
      icon: LucideArrowLeft,
      hint: "Shift+<",
      perform: () => goToPreviousTicket(),
    });
  }
  return commands;
}

function statusChildren(ticketId: string): Command[] {
  return statusOptions("Set status", (status) =>
    updateTicket(ticketId, { status })
  );
}

function priorityChildren(ticketId: string): Command[] {
  return priorityOptions("Set priority", (priority) =>
    updateTicket(ticketId, { priority })
  );
}

async function agentChildren(ticketId: string): Promise<Command[]> {
  const store = useAgentStore();
  if (!store.agents.data) await store.agents.reload();
  return (store.agents.data ?? []).map((agent) => ({
    id: `agent-${agent.name}`,
    title: agent.agent_name || agent.name,
    // agent_name is often just the email; don't print it twice.
    subtitle: agent.agent_name === agent.name ? "" : agent.name,
    group: "Assign to",
    icon: LucideUserPlus,
    perform: () => assignTicket(ticketId, agent.name),
  }));
}

const teams = createListResource({
  doctype: "HD Team",
  fields: ["name"],
  pageLength: 100,
});

async function teamChildren(ticketId: string): Promise<Command[]> {
  if (!teams.data) await teams.reload();
  return (teams.data ?? []).map((team) => ({
    id: `team-${team.name}`,
    title: team.name,
    group: "Set team",
    icon: LucideUsers,
    perform: () => updateTicket(ticketId, { agent_group: team.name }),
  }));
}

const ticketTypes = createListResource({
  doctype: "HD Ticket Type",
  fields: ["name"],
  pageLength: 100,
});

async function ticketTypeChildren(ticketId: string): Promise<Command[]> {
  if (!ticketTypes.data) await ticketTypes.reload();
  return (ticketTypes.data ?? []).map((type) => ({
    id: `type-${type.name}`,
    title: type.name,
    group: "Set type",
    icon: LucideTag,
    perform: () => updateTicket(ticketId, { ticket_type: type.name }),
  }));
}

function updateTicket(ticketId: string, changes: Record<string, string>): void {
  const { ticket, activities } = useTicket(ticketId);
  const [field] = Object.keys(changes);
  if (ticket.doc?.[field] === changes[field]) return;
  ticket.setValue.submit(changes, {
    onSuccess: () => activities.reload(),
  });
}

const assignResource = createResource({
  url: "frappe.desk.form.assign_to.add",
});

async function assignTicket(ticketId: string, agent: string): Promise<void> {
  const { assignees, activities } = useTicket(ticketId);
  try {
    await assignResource.submit({
      doctype: "HD Ticket",
      name: ticketId,
      assign_to: [agent],
    });
    toast.success(__("Assignees updated successfully."));
    assignees.reload();
    activities.reload();
  } catch {
    toast.error(__("Failed to update Assignees."));
  }
}

// ponytail: "Delete ticket" deliberately stays out of the palette. It needs a
// confirm dialog, and $dialog is only reachable via globalStore(), which calls
// getCurrentInstance() and is therefore unsafe from module scope. The ticket
// header already offers it. Wire it here if a confirm helper lands in frappe-ui.

