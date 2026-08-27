import {
  replyComposer,
  showEmailBox,
  toggleEmailBox,
} from "@/pages/ticket/modalStates";
import { capture } from "@/telemetry";
import { __ } from "@/translation";
import { RenderedSavedReply } from "@/types";
import { createListResource, createResource, toast } from "frappe-ui";
import { nextTick } from "vue";
import {
  CONTEXT_WEIGHT,
  FLAT_OPTION_WEIGHT,
  GROUP,
  type Command,
} from "./paletteTypes";
import {
  mostUsedFirst,
  topSavedReplies,
  withUse,
  withoutReply,
  type SavedReplyUsage,
} from "./savedReplyRanking";
import { userStorage } from "@/composables/userStorage";

import LucideMessageSquareQuote from "~icons/lucide/message-square-quote";

interface SavedReplyRow {
  name: string;
  title: string;
}

/** What it takes to earn a root-level row, rather than guessing at one. */
const FLAT_MIN_USES = 5;
const FLAT_MAX_ROWS = 3;

// A bare noun leading with "Saved": the prefix match keeps this row above the
// individual replies on a "saved" query (pinned in fuzzyScore.check.ts).
const GROUP_TITLE = "Saved Replies";
const SUBTITLE = "Saved Reply";

/** Drills into saved replies, then opens the composer pre-filled — never
 * send-on-select; the agent must see what goes to a customer. */
export function savedReplyCommands(ticketId: string): Command[] {
  return [
    {
      id: "ticket-saved-reply",
      title: __(GROUP_TITLE),
      group: GROUP.ticket,
      weight: CONTEXT_WEIGHT,
      icon: LucideMessageSquareQuote,
      // "reply" singular is not a substring of "replies".
      keywords: "reply template canned macro snippet",
      children: () => savedReplyChildren(ticketId),
    },
    ...topSavedReplyCommands(ticketId),
  ];
}

const savedReplies = createListResource({
  doctype: "HD Saved Reply",
  fields: ["name", "title"],
  // Unfiltered by scope: the server already limits this to what the agent may use.
  orderBy: "modified desc",
  pageLength: 999,
});

/** Inside this level the query filters replies only — no ticket/command collisions. */
async function savedReplyChildren(ticketId: string): Promise<Command[]> {
  if (!savedReplies.data) await savedReplies.reload();
  const replies = (savedReplies.data ?? []) as SavedReplyRow[];
  return mostUsedFirst(replies, usage.value).map((reply) => ({
    id: `saved-reply-${reply.name}`,
    title: reply.title,
    group: GROUP_TITLE,
    icon: LucideMessageSquareQuote,
    perform: () => applySavedReply(ticketId, reply.name, reply.title),
  }));
}

/** Most-used replies as root rows, titled from the usage record — no fetch,
 * nothing to block the root build. */
function topSavedReplyCommands(ticketId: string): Command[] {
  return topSavedReplies(usage.value, FLAT_MIN_USES, FLAT_MAX_ROWS).map(
    (reply) => ({
      id: `saved-reply-flat-${reply.name}`,
      title: reply.title,
      // Subtitle, not title prefix: a bare reply title at root reads as a ticket.
      subtitle: __(SUBTITLE),
      group: "Frequent replies",
      icon: LucideMessageSquareQuote,
      hideWhenEmpty: true,
      weight: FLAT_OPTION_WEIGHT,
      perform: () => applySavedReply(ticketId, reply.name, reply.title),
    })
  );
}

const renderSavedReply = createResource({
  url: "helpdesk.api.saved_replies.get_rendered_saved_reply",
});

async function applySavedReply(
  ticketId: string,
  replyId: string,
  title: string
): Promise<void> {
  let reply: RenderedSavedReply;
  try {
    reply = await renderSavedReply.submit({
      saved_reply_id: replyId,
      ticket_id: ticketId,
    });
  } catch {
    // A reply deleted after it earned a flat row would otherwise fail forever.
    forgetSavedReply(replyId);
    toast.error(__("Could not load {0}", title));
    return;
  }

  // Toggle would *close* an already-open composer, discarding a draft.
  if (!showEmailBox.value) toggleEmailBox();
  await nextTick(); // v-show has to reveal the editor before it can take focus

  const insert = replyComposer.value;
  if (!insert) {
    toast.error(__("Could not open the reply box"));
    return;
  }
  insert(reply);
  recordSavedReplyUse(replyId, title);
  capture("saved_reply_applied", { data: { source: "command_palette" } });
}

// --- per-agent usage -----------------------------------------------------

const usage = userStorage<SavedReplyUsage>("hd_saved_reply_uses", {});

/** Also called by the composer's selector modal, so promotion counts both surfaces. */
export function recordSavedReplyUse(replyId: string, title: string): void {
  usage.value = withUse(usage.value, replyId, title);
}

function forgetSavedReply(replyId: string): void {
  usage.value = withoutReply(usage.value, replyId);
}
