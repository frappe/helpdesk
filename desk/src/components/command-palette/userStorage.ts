import { useStorage } from "@vueuse/core";

/** localStorage scoped to the signed-in agent, so nothing personal survives a
 * shift handover. Reads the session cookie, not the auth store — this runs at
 * module load, before pinia exists. */
export function userStorage<T>(key: string, fallback: T) {
  return useStorage<T>(`${key}:${sessionUserId()}`, fallback);
}

function sessionUserId(): string {
  const cookies = new URLSearchParams(document.cookie.split("; ").join("&"));
  return cookies.get("user_id") || "guest";
}
