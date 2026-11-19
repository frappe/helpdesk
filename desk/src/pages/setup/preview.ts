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

const avatar = (name: string) => `/assets/helpdesk/desk/demo/${name}.svg`;

/** The sample people's avatars, made once with DiceBear Notionists (CC0) and committed, like Gameplan's demo. */
const SAMPLE_AVATARS: Record<string, string> = {
  [SAMPLE_TICKET.customer]: avatar("daniel"),
  "sam@example.com": avatar("sam"),
  "maya@example.com": avatar("maya"),
  "priya@example.com": avatar("priya"),
  "leo@example.com": avatar("leo"),
};

/** A sample person's avatar; real people have none here, so their initials show. */
export const avatarUrl = (person: string) => SAMPLE_AVATARS[person];
