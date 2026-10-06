// The knowledge base settings' Preview stores the unsaved look here and opens the portal with
// ?preview=1. The tab remembers it, so the draft stays on as the reader moves between pages.
export const KB_PREVIEW_KEY = "kb:preview";

export type KbPreview = {
  banner_image: string;
  banner_preset: string;
  pinned: string[];
  links: { label: string; url: string; open_in_new_tab: boolean }[];
};

export function readKbPreview(): KbPreview | null {
  try {
    if (new URLSearchParams(location.search).has("preview")) {
      sessionStorage.setItem(KB_PREVIEW_KEY, "1");
    }
    if (!sessionStorage.getItem(KB_PREVIEW_KEY)) return null;
    return JSON.parse(localStorage.getItem(KB_PREVIEW_KEY) || "null");
  } catch {
    return null;
  }
}
