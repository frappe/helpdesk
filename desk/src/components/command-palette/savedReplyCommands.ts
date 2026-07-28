import { replyComposer } from "@/components/replyComposer";
import { showEmailBox, toggleEmailBox } from "@/pages/ticket/modalStates";
import { capture } from "@/telemetry";
import { __ } from "@/translation";
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
import { userStorage } from "./userStorage";

import LucideMessageSquareQuote from "~icons/lucide/message-square-quote";

interface SavedReplyRow {
  name: string;
  title: string;
}

/** What it takes to earn a root-level row, rather than guessing at one. */
const FLAT_MIN_USES = 5;
const FLAT_MAX_ROWS = 3;

/**
 * "Insert", not "Reply with": it says what actually happens — the reply lands in
 * the composer and the agent still has to send it. It also keeps the word "reply"
 * out of the title, which matters for ranking (see fuzzyScore.check.ts): three
 * rows in the reply family used to cluster at the top of a "reply" query.
 */
const GROUP_TITLE = "Insert saved reply";

/**
 * Composing replies is the bulk of an agent's day, and the palette did not touch
 * it: `Reply to ticket` opened an empty box. This drills into the saved replies,
 * then opens the composer pre-filled — never send-on-select, because the agent
 * has to see what goes to a customer.
 */
export function savedReplyCommands(ticketId: string): Command[] {
  return [
    {
      id: "ticket-saved-reply",
      title: __(GROUP_TITLE),
      group: GROUP.ticket,
      weight: CONTEXT_WEIGHT,
      icon: LucideMessageSquareQuote,
      keywords: "template canned macro snippet",
      children: () => savedReplyChildren(ticketId),
    },
    ...topSavedReplyCommands(ticketId),
  ];
}

const savedReplies = createListResource({
  doctype: "HD Saved Reply",
  fields: ["name", "title"],
  // Unfiltered by scope: the server already limits this to what the agent may
  // use, and a palette that hides usable replies is worse than a long list.
  orderBy: "modified desc",
  pageLength: 999,
});

/**
 * A drill-down is a scoped search, not a consolation prize. Saved replies are
 * unbounded and content-named, so inside this level the query filters replies
 * only — zero collision with tickets or commands.
 */
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

/**
 * The most-used replies as root-level rows, so the common case skips the
 * drill-down entirely. Titles come from the usage record rather than the list
 * resource, so a root row costs no fetch and cannot block the root build.
 */
function topSavedReplyCommands(ticketId: string): Command[] {
  return topSavedReplies(usage.value, FLAT_MIN_USES, FLAT_MAX_ROWS).map(
    (reply) => ({
      id: `saved-reply-flat-${reply.name}`,
      // Composed, like the other flat rows: a bare "Refund policy" reads as a
      // ticket rather than as something that happens when you press Enter. The
      // prefix must match the parent's verb — "Reply: X" under an "Insert saved
      // reply" parent scored *above* it, inverting the intended hierarchy.
      title: __("Insert: {0}", reply.title),
      group: GROUP.ticket,
      icon: LucideMessageSquareQuote,
      keywords: reply.title,
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
  let html: string;
  try {
    html = await renderSavedReply.submit({
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
  insert(html);
  recordSavedReplyUse(replyId, title);
  capture("saved_reply_applied", { data: { source: "command_palette" } });
}

// --- per-agent usage -----------------------------------------------------

/**
 * Frequency, per agent. Deliberately not frecency: frequency describes the
 * stable core set, and the case it misses — five password resets in a row —
 * needs recency decay, which is not worth building before anyone reports it.
 *
 * Per-device, being localStorage. If hot-desking makes that bite, this moves to
 * a per-agent usage record server-side. A counter on `HD Saved Reply` would not
 * do: that answers a team-wide question, not a personal one.
 */
const usage = userStorage<SavedReplyUsage>("hd_saved_reply_uses", {});

function recordSavedReplyUse(replyId: string, title: string): void {
  usage.value = withUse(usage.value, replyId, title);
}

function forgetSavedReply(replyId: string): void {
  usage.value = withoutReply(usage.value, replyId);
}
