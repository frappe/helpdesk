import type { Api } from "./api";
import { seedPersonas } from "./personas";

export const OUTGOING_EMAIL = "e2e-support@example.com";

/** Baseline every spec relies on; safe to run on an already seeded site. */
export async function seedSite(api: Api) {
  await seedPersonas(api);
  await ensureOutgoingEmailAccount(api);
  await api.update("HD Settings", "HD Settings", {
    persona_captured: 1,
    setup_complete: 1,
  });
}

// SMTP is never reached: without a password Frappe skips the connection check
// and queued mails just sit in the Email Queue.
async function ensureOutgoingEmailAccount(api: Api) {
  if (await api.exists("Email Account", { email_id: OUTGOING_EMAIL })) return;
  await api.insert("Email Account", {
    email_account_name: "E2E Support",
    email_id: OUTGOING_EMAIL,
    smtp_server: "smtp.example.invalid",
    no_smtp_authentication: 1,
    enable_outgoing: 1,
    default_outgoing: 1,
    enable_incoming: 0,
  });
}
