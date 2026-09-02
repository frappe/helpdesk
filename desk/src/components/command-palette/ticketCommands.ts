import { useNotifyTicketUpdate } from "@/composables/realtime";
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
import { getMeta } from "@/stores/meta";
import { capture } from "@/telemetry";
import { __ } from "@/translation";
import { copyToClipboard } from "@/utils";
import { call, createListResource, createResource, toast } from "frappe-ui";
import { priorityOptions, statusOptions } from "./optionCommands";
import {
  CONTEXT_WEIGHT,
  FLAT_OPTION_WEIGHT,
  GROUP,
  type Command,
} from "./paletteTypes";
import { savedReplyCommands } from "./savedReplyCommands";
import { tagChildren } from "./tagCommands";

// Same icons as the composer buttons these rows press.
import { CommentIcon, EmailIcon } from "@/components/icons/";
import LucideArrowLeft from "~icons/lucide/arrow-left";
import LucideArrowRight from "~icons/lucide/arrow-right";
import LucideCircleDot from "~icons/lucide/circle-dot";
import LucideCopy from "~icons/lucide/copy";
import LucideFlag from "~icons/lucide/flag";
import LucideLink from "~icons/lucide/link";
import LucideMerge from "~icons/lucide/merge";
import LucideShapes from "~icons/lucide/shapes";
import LucideTags from "~icons/lucide/tags";
import LucideUserPlus from "~icons/lucide/user-plus";
import LucideUsers from "~icons/lucide/users";

// --- ticket context ------------------------------------------------------

/** Actions on the open ticket. `weight` keeps them above fixed-rank search hits. */
export function ticketCommands(ticketId: string): Command[] {
  const commands: Command[] = [
    {
      id: "ticket-status",
      title: __("Change status"),
      group: GROUP.ticket,
      weight: CONTEXT_WEIGHT,
      icon: LucideCircleDot,
      hint: "S",
      // No option names: the flat "Set status: Open" rows own those terms.
      keywords: "state",
      children: () => statusChildren(ticketId),
    },
    {
      id: "ticket-priority",
      title: __("Change priority"),
      group: GROUP.ticket,
      weight: CONTEXT_WEIGHT,
      icon: LucideFlag,
      hint: "P",
      keywords: "level",
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
    ...assignToMeCommand(ticketId),
    {
      id: "ticket-team",
      title: __("Change team"),
      group: GROUP.ticket,
      weight: CONTEXT_WEIGHT,
      icon: LucideUsers,
      hint: "Shift+T",
      keywords: "group agent_group escalation escalate",
      children: () => teamChildren(ticketId),
    },
    {
      id: "ticket-type",
      title: __("Change type"),
      group: GROUP.ticket,
      weight: CONTEXT_WEIGHT,
      icon: LucideShapes,
      hint: "T",
      children: () => ticketTypeChildren(ticketId),
    },
    {
      id: "ticket-tags",
      title: __("Tags"),
      group: GROUP.ticket,
      weight: CONTEXT_WEIGHT,
      icon: LucideTags,
      hint: "G",
      keywords: "add remove label categorise",
      children: () => tagChildren(ticketId),
    },
    {
      id: "ticket-comment",
      title: __("Add comment"),
      group: GROUP.ticket,
      weight: CONTEXT_WEIGHT,
      icon: CommentIcon,
      hint: "C",
      keywords: "note internal",
      perform: () => toggleCommentBox(),
    },
    {
      id: "ticket-reply",
      title: __("Reply to ticket"),
      group: GROUP.ticket,
      weight: CONTEXT_WEIGHT,
      icon: EmailIcon,
      hint: "R",
      keywords: "email respond",
      perform: () => toggleEmailBox(),
    },
    ...savedReplyCommands(ticketId),
    ...flatOptionCommands(ticketId),
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

/** Skips the agent drill-down; hidden once held — "Assign to" is the way back out. */
function assignToMeCommand(ticketId: string): Command[] {
  const me = window.agent;
  if (!me || assignedNames(ticketId).includes(me)) return [];
  return [
    {
      id: "ticket-assign-me",
      title: __("Assign to me"),
      group: GROUP.ticket,
      weight: CONTEXT_WEIGHT,
      icon: LucideUserPlus,
      keywords: "claim mine myself take",
      perform: () => assignTicket(ticketId, me),
    },
  ];
}

/** Same guards as the ticket header's own Merge action. */
function mergeCommand(ticketId: string): Command[] {
  const doc = useTicket(ticketId).ticket.doc;
  const mergeable =
    doc &&
    !doc.is_merged &&
    ["Open", "Paused"].includes(doc.status_category ?? "");
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

/** Every option as a root row, so "urgent" sets the priority without a picker;
 * hidden until typed — the drill-downs stay the discoverable path. */
function flatOptionCommands(ticketId: string): Command[] {
  const { doc } = useTicket(ticketId).ticket;
  const flat = { hideWhenEmpty: true, weight: FLAT_OPTION_WEIGHT };
  return [
    ...statusOptions({
      ...flat,
      group: GROUP.ticket,
      titlePrefix: "Set status",
      current: doc?.status,
      onPick: (status) => updateTicket(ticketId, { status }),
    }),
    ...priorityOptions({
      ...flat,
      group: GROUP.ticket,
      titlePrefix: "Set priority",
      current: doc?.priority,
      onPick: (priority) => updateTicket(ticketId, { priority }),
    }),
  ];
}

function statusChildren(ticketId: string): Command[] {
  return statusOptions({
    group: "Set status",
    current: useTicket(ticketId).ticket.doc?.status,
    onPick: (status) => updateTicket(ticketId, { status }),
  });
}

function priorityChildren(ticketId: string): Command[] {
  return priorityOptions({
    group: "Set priority",
    current: useTicket(ticketId).ticket.doc?.priority,
    onPick: (priority) => updateTicket(ticketId, { priority }),
  });
}

async function agentChildren(ticketId: string): Promise<Command[]> {
  const store = useAgentStore();
  if (!store.agents.data) await store.agents.reload();
  const assigned = assignedNames(ticketId);
  return (store.agents.data ?? []).map((agent) => ({
    id: `agent-${agent.name}`,
    title: agent.agent_name || agent.name,
    // agent_name is often just the email; don't print it twice.
    subtitle: agent.agent_name === agent.name ? "" : agent.name,
    group: "Assign to",
    avatar: {
      image: agent.user_image,
      label: agent.agent_name || agent.name,
    },
    // Rows add, never replace — the tick is how you tell which it will do.
    checked: assigned.includes(agent.name),
    perform: () => assignTicket(ticketId, agent.name),
  }));
}

function assignedNames(ticketId: string): string[] {
  return (useTicket(ticketId).assignees.data ?? []).map(
    (assignee) => assignee.name
  );
}

const teams = createListResource({
  doctype: "HD Team",
  fields: ["name"],
  pageLength: 100,
});

async function teamChildren(ticketId: string): Promise<Command[]> {
  if (!teams.data) await teams.reload();
  const current = useTicket(ticketId).ticket.doc?.agent_group;
  return (teams.data ?? []).map((team) => ({
    id: `team-${team.name}`,
    title: team.name,
    group: "Set team",
    checked: team.name === current,
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
  const current = useTicket(ticketId).ticket.doc?.ticket_type;
  return (ticketTypes.data ?? []).map((type) => ({
    id: `type-${type.name}`,
    title: type.name,
    group: "Set type",
    checked: type.name === current,
    perform: () => updateTicket(ticketId, { ticket_type: type.name }),
  }));
}

// Module scope is safe: getMeta is cached per doctype and shares the fetch.
const ticketMeta = getMeta("HD Ticket");

/** From meta, so a site that relabels Team gets its own word in the broadcast. */
function fieldLabel(fieldname: string): string {
  return ticketMeta.getField(fieldname)?.label ?? fieldname;
}

function updateTicket(ticketId: string, changes: Record<string, string>): void {
  const [field, value] = Object.entries(changes)[0] ?? [];
  if (!field || value === undefined) return;
  const { ticket, activities } = useTicket(ticketId);
  const current = ticket.doc as unknown as Record<string, unknown> | undefined;
  // The drill-down already ticks the current value, so picking it again just
  // closes quietly.
  if (current?.[field] === value) return;
  // Same order as the details tab: tell co-viewers, then write.
  useNotifyTicketUpdate(ticketId).notifyTicketUpdate(fieldLabel(field), value);
  ticket.setValue.submit(changes, {
    onSuccess: () => activities.reload(),
  });
}

const addAssignee = createResource({ url: "frappe.desk.form.assign_to.add" });

/** Adds without dropping existing assignees; unassigning stays with the AssignTo
 * widget. Mirrors the popover's activity log so both surfaces leave one trail. */
async function assignTicket(ticketId: string, agent: string): Promise<void> {
  const { assignees, activities } = useTicket(ticketId);
  if (assignedNames(ticketId).includes(agent)) {
    toast.success(__("Already assigned to {0}", agent));
    return;
  }
  try {
    await addAssignee.submit({
      doctype: "HD Ticket",
      name: ticketId,
      assign_to: [agent],
    });
    capture("ticket_assigned", {
      data: { doctype: "HD Ticket", source: "command_palette" },
    });
    await logAssignment(ticketId, agent);
    toast.success(__("Assignees updated successfully."));
    assignees.reload();
    activities.reload();
  } catch {
    toast.error(__("Failed to update Assignees."));
  }
}

function logAssignment(ticketId: string, agent: string): Promise<unknown> {
  return call("frappe.client.insert", {
    doc: {
      doctype: "HD Ticket Activity",
      ticket: ticketId,
      action: `assigned ${agent}`,
    },
  });
}
