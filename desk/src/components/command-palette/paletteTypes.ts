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
  children?: () => Command[] | Promise<Command[]>;
  perform?: () => void;
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

/** Ticket-context rows outrank server search hits (fixed rank ~950). */
export const CONTEXT_WEIGHT = 1.2;

/** Untranslated: the palette translates group labels once, at render. */
export const GROUP = {
  ticket: "Ticket",
  list: "Ticket list",
  recent: "Recent",
  results: "Tickets",
  navigate: "Navigate",
  create: "Create",
  account: "Account",
};

export const FALLBACK_GROUP = "No results";
