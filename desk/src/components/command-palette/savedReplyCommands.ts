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
 * A bare noun, not a verb phrase. This row opens a category, the same way the
 * `Settings` row does, and it is what the product calls the feature everywhere
 * else — so there is no invented verb to keep in sync with the settings tab.
 *
 * Leading with "Saved" also keeps this row above the individual replies on a
 * "saved" query: both get a prefix match, so `CONTEXT_WEIGHT` decides. A
 * mid-title verb would not — "Insert saved reply" only reaches a word-boundary
 * match (~950) and loses to any root row starting with "Saved".
 * `fuzzyScore.check.ts` pins both cases.
 */
const GROUP_TITLE = "Saved Replies";
const SUBTITLE = "Saved Reply";

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
      // "reply" singular is not a substring of "replies", so without it here the
      // row is unreachable by the most obvious thing an agent would type.
      keywords: "reply template canned macro snippet",
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
      title: reply.title,
      // The qualifier belongs here rather than in the title: a bare "Refund
      // policy" at root would read as a ticket, but as a title prefix it spends
      // the first characters on chrome before the word the agent typed. Muted
      // and right-aligned, the same way search rows carry "Open · #0484".
      subtitle: __(SUBTITLE),
      // Own titled section: these rows are promoted by usage, and without a
      // header a lone reply title at root reads as a random ticket. "Replies"
      // stays out of the header — the per-row subtitle already says it.
      group: "Most used",
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

/** Exported for the composer's selector modal: usage counts from both surfaces
 * feed the same record, so palette promotion reflects how an agent actually
 * works, not just their palette picks. */
export function recordSavedReplyUse(replyId: string, title: string): void {
  usage.value = withUse(usage.value, replyId, title);
}

function forgetSavedReply(replyId: string): void {
  usage.value = withoutReply(usage.value, replyId);
}
