import { __ } from "@/translation";

/** The made-up ticket the preview walks through; the real first ticket shows on the Email step. */
export const SAMPLE_TICKET = {
  id: "1042",
  subject: __("Can't reset my password"),
  customer: "Daniel Ortiz",
  email: "daniel.ortiz@example.com",
  message: [
    __("Hi,"),
    __(
      "The reset link in your email says it has expired. Could you send me a new one? I need to get into my account before Friday's billing run."
    ),
    __("Thanks, Daniel"),
  ],
  reply: [
    __("Hi Daniel,"),
    __("Here's a fresh reset link. It stays valid for 24 hours."),
  ],
  draft: __("Hi Daniel, we are looking into this issue."),
};

export const nameOf = (email: string) => {
  const local = email.split("@")[0];
  return local.charAt(0).toUpperCase() + local.slice(1);
};

const SAMPLE_DOMAIN = "@example.com";
const AVATAR_BACKGROUNDS = "b6e3f4,c0aede,d1d4f9,ffd5dc,ffdfbf";

/** A DiceBear avatar; anyone but the made-up sample people is hashed, so no real name or address leaves the browser. */
export function avatarUrl(person: string) {
  const sample =
    person.endsWith(SAMPLE_DOMAIN) || person === SAMPLE_TICKET.customer;
  const seed = sample ? person : `hd-${fnv1a(person.toLowerCase())}`;
  return `https://api.dicebear.com/9.x/notionists/svg?seed=${encodeURIComponent(
    seed
  )}&backgroundColor=${AVATAR_BACKGROUNDS}`;
}

function fnv1a(text: string) {
  let hash = 0x811c9dc5;
  for (const char of text) {
    hash ^= char.codePointAt(0)!;
    hash = Math.imul(hash, 0x01000193);
  }
  return (hash >>> 0).toString(36);
}
