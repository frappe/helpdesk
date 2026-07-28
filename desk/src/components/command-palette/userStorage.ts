import { useStorage } from "@vueuse/core";

/**
 * localStorage scoped to the signed-in agent. Support desks hot-desk, so
 * anything personal — the tickets you visited, the replies you send most —
 * must not survive a shift handover on a shared machine.
 *
 * Read from the session cookie rather than the auth store: this runs at module
 * load, before pinia is installed, and the key has to be right on the very
 * first read or the unscoped value is what gets migrated forward.
 */
export function userStorage<T>(key: string, fallback: T) {
  return useStorage<T>(`${key}:${sessionUserId()}`, fallback);
}

function sessionUserId(): string {
  const cookies = new URLSearchParams(document.cookie.split("; ").join("&"));
  return cookies.get("user_id") || "guest";
}
