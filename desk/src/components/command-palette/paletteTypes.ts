import type { Component } from "vue";

export interface Command {
  id: string;
  title: string;
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
  /** Fixed score, bypassing the fuzzy scorer. Server hits arrive pre-ranked. */
  rank?: number;
  /**
   * The title as the server highlighted it, `<mark>` runs included. `title`
   * stays plain, since that is what gets scored and read out.
   */
  marked?: string;
  /** Renders a trailing tick: this row's value is already set on the ticket. */
  checked?: boolean;
  /**
   * Perform without closing; the tick flips optimistically and flips back if
   * `perform` throws. For toggle rows (tags) where one visit flips several.
   */
  keepOpen?: boolean;
  /**
   * Hidden until the user types. Weight can't express this — an empty term
   * scores 0 before weight applies, so every row would tie at the root.
   */
  hideWhenEmpty?: boolean;
  children?: () => Command[] | Promise<Command[]>;
  perform?: () => void;
}

/**
 * The record the palette is acting on, shown as a removable chip above the
 * input. Present means the list is scoped to that record's commands.
 */
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

/**
 * Splits the server's `<mark>` highlighting into runs, so a search row can show
 * *why* it matched. Rendered as text nodes — no `v-html`, so no sanitiser and no
 * way for ticket content to inject markup. Any other tags are stripped.
 */
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

/**
 * Flat option rows ("Set priority: Urgent") sit above search hits but below the
 * drill-down parent, so typing "priority" still leads with "Change priority"
 * while typing "urgent" leads with the row that sets it.
 */
export const FLAT_OPTION_WEIGHT = 1.15;

/** Untranslated: the palette translates group labels once, at render. */
export const GROUP = {
  ticket: "Ticket",
  list: "Ticket list",
  recent: "Recent",
  results: "Tickets",
  navigate: "Navigate",
  // Untitled: "New ticket" already says create, a header would repeat it.
  create: "",
  account: "Account",
};

