// Settings Preview stores the unsaved look here; `?preview=1` enables it per tab.
export const KNOWLEDGE_BASE_PREVIEW_KEY = "kb:preview";

export type KnowledgeBasePreview = {
  banner_image: string;
  banner_preset: string;
  pinned: string[];
  links: { label: string; url: string; open_in_new_tab: boolean }[];
};

export function readKnowledgeBasePreview(): KnowledgeBasePreview | null {
  try {
    if (new URLSearchParams(location.search).has("preview")) {
      sessionStorage.setItem(KNOWLEDGE_BASE_PREVIEW_KEY, "1");
    }
    if (!sessionStorage.getItem(KNOWLEDGE_BASE_PREVIEW_KEY)) return null;
    return JSON.parse(localStorage.getItem(KNOWLEDGE_BASE_PREVIEW_KEY) || "null");
  } catch {
    return null;
  }
}
