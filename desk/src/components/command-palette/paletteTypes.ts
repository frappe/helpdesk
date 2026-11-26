import type { Component } from "vue";

export interface Command {
  id: string;
  title: string;
  /** Rendered inline after the title in muted ink; not part of fuzzy scoring. */
  titleSuffix?: string;
  group: string;
  icon?: Component;
  /** Props bound to `icon`, for icons that render from data (e.g. priority level). */
  iconProps?: Record<string, unknown>;
  subtitle?: string;
  keywords?: string;
  /** Combo string rendered by ShortcutKey, e.g. "Mod+." */
  hint?: string;
  /** Multiplies the fuzzy score; <1 sinks a row once the user types. */
  weight?: number;
  /** Tailwind class for the leading colour dot (status/priority rows). */
  dotClass?: string;
  /** Leading avatar (agent rows); `label` initials are the no-photo fallback. */
  avatar?: { image?: string; label: string };
  /** Fixed score, bypassing the fuzzy scorer. Server hits arrive pre-ranked. */
  rank?: number;
  /** Server-highlighted title with `<mark>` runs; `title` stays plain for scoring. */
  marked?: string;
  /** Renders a trailing tick: this row's value is already set on the ticket. */
  checked?: boolean;
  /** Perform, then pop back a level; the optimistic tick flips back if `perform` throws. */
  keepOpen?: boolean;
  /** Hidden until typed, and only a substring-or-better match reveals it. */
  hideWhenEmpty?: boolean;
  children?: () => Command[] | Promise<Command[]>;
  perform?: () => void;
}

/** The record the palette acts on, shown as the removable chip above the input. */
export interface PaletteContext {
  /** Ticket name, passed to the command builders. */
  id: string;
  /** Short identifier on the chip, e.g. "#13". */
  label: string;
  /** Human title on the chip; empty until the ticket resource resolves. */
  title: string;
}

export interface SearchItem {
  doctype: string;
  name: string;
  title?: string;
  content?: string;
  status?: string;
  priority?: string;
  reference_ticket?: string;
  reference_name?: string;
}

/** Server highlights matches with <mark>; palette rows render plain text. */
export function stripTags(value: string): string {
  return (value ?? "").replace(/<[^>]*>/g, "");
}

export interface TitleRun {
  text: string;
  /** Part of what the query matched, per the server's own highlighting. */
  match: boolean;
}

/** Splits `<mark>` highlighting into runs, rendered as text nodes — no v-html,
 * so ticket content cannot inject markup. */
export function titleRuns(marked: string): TitleRun[] {
  return (marked ?? "")
    .split(/(<mark>[\s\S]*?<\/mark>)/g)
    .map((part) => ({
      text: stripTags(part),
      match: part.startsWith("<mark>"),
    }))
    .filter((run) => run.text.length > 0);
}

/** Ticket-context rows outrank server search hits (fixed rank ~950). */
export const CONTEXT_WEIGHT = 1.2;

/** Above search hits, below the drill-down parent: "priority" leads with the
 * picker, "urgent" with the row that sets it. */
export const FLAT_OPTION_WEIGHT = 1.15;

/** Untranslated: the palette translates group labels once, at render. */
export const GROUP = {
  ticket: "Ticket",
  list: "Ticket list",
  recent: "Recent tickets",
  results: "Tickets",
  navigate: "Navigate",
  // Untitled: "New ticket" already says create, a header would repeat it.
  create: "",
  account: "Account",
};

