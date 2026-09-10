import type { Recipient } from "@framework/ui/components/Composer/index.ts";

// Bare addresses and the `Name <email>` form the timeline hands over.
export function toRecipient(address: string): Recipient {
  const match = address.match(/^\s*"?([^"<]*?)"?\s*<([^>]+)>\s*$/);
  if (!match) return { email: address.trim() };
  const label = match[1].trim();
  return { email: match[2].trim(), ...(label && { label }) };
}

export function toRecipientList(addresses: unknown[] | undefined): Recipient[] {
  return (addresses ?? [])
    .filter(Boolean)
    .map((address) => toRecipient(String(address)));
}
