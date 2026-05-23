import { call, toast } from "frappe-ui";
import { __ } from "@/translation";

export interface CustomServerFields {
  email_server: string;
  smtp_server: string;
  incoming_port: string;
  smtp_port: string;
  use_ssl: boolean;
  use_imap: boolean;
  use_ssl_for_outgoing: boolean;
}

export async function syncCustomServerFromDomain(
  domain: string,
  target: CustomServerFields
): Promise<void> {
  if (!domain) return;
  try {
    const doc = await call("frappe.client.get", {
      doctype: "Email Domain",
      name: domain,
    });
    target.email_server = doc.email_server ?? target.email_server;
    target.smtp_server = doc.smtp_server ?? target.smtp_server;
    target.incoming_port = String(doc.incoming_port ?? target.incoming_port);
    target.smtp_port = String(doc.smtp_port ?? target.smtp_port);
    target.use_ssl = Boolean(doc.use_ssl ?? target.use_ssl);
    target.use_imap = Boolean(doc.use_imap ?? target.use_imap);
    target.use_ssl_for_outgoing = Boolean(
      doc.use_ssl_for_outgoing ?? target.use_ssl_for_outgoing
    );
  } catch {
    toast.error(__("Failed to load Email Domain"));
  }
}

export function openDomainCreate(close?: () => void): void {
  close?.();
  window.open(
    "/desk/email-domain/new-email-domain",
    "_blank",
    "noopener,noreferrer"
  );
}

export function openDomainEdit(domain: string): void {
  if (!domain) return;
  window.open(
    `/desk/email-domain/${encodeURIComponent(domain)}`,
    "_blank",
    "noopener,noreferrer"
  );
}
