import type { Role } from "@/components/Settings/inviteRoles";
import { __ } from "@/translation";
import zod from "zod";

export type InviteRow = {
  id: number;
  email: string;
  role: Role;
  sent: boolean;
};

export const MAX_INVITE_ROWS = 20;

let nextRowId = 1;
export const createInviteRow = (): InviteRow => ({
  id: nextRowId++,
  email: "",
  role: "Agent",
  sent: false,
});

export const normalizeEmail = (email: string) => email.trim().toLowerCase();

const isEmail = (email: string) => zod.string().email().safeParse(email).success;

/** Per-row errors; blank rows are ignored and a repeated address is flagged. */
export function validateRows(rows: InviteRow[]): {
  errors: Record<number, string>;
  duplicates: Set<number>;
} {
  const errors: Record<number, string> = {};
  const duplicates = new Set<number>();
  const seen = new Set<string>();

  for (const row of rows) {
    const email = normalizeEmail(row.email);
    if (!email) continue;
    if (!isEmail(email)) {
      errors[row.id] = __("Enter a valid email address");
    } else if (seen.has(email)) {
      duplicates.add(row.id);
      errors[row.id] = __("This email is already in the list");
    }
    seen.add(email);
  }
  return { errors, duplicates };
}

/** How many valid addresses a send would invite right now. */
export function countSendable(rows: InviteRow[]): number {
  const { errors } = validateRows(rows);
  const valid = rows.filter((row) => !errors[row.id]);
  return Object.values(groupUnsentByRole(valid)).reduce(
    (total, emails) => total + (emails?.length ?? 0),
    0
  );
}

/** Addresses still to send, per role. Sent, blank and repeated rows are left out. */
export function groupUnsentByRole(
  rows: InviteRow[]
): Partial<Record<Role, string[]>> {
  const seen = new Set(
    rows.filter((row) => row.sent).map((row) => normalizeEmail(row.email))
  );
  const groups: Partial<Record<Role, string[]>> = {};

  for (const row of rows) {
    const email = normalizeEmail(row.email);
    if (row.sent || !email || seen.has(email)) continue;
    seen.add(email);
    (groups[row.role] ??= []).push(email);
  }
  return groups;
}

/** The valid, unique addresses typed so far, for the preview. */
export function previewInvitees(rows: InviteRow[]): string[] {
  const emails = rows.map((row) => normalizeEmail(row.email));
  return [...new Set(emails.filter(isEmail))];
}
