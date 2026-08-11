import { RenderedSavedReply } from "@/types";
import { shallowRef } from "vue";

/**
 * The mounted reply composer's "insert this saved reply" action, published for
 * whoever is outside the ticket page's provide chain — which is the command
 * palette, mounted in AppSidebar and therefore unable to `inject` anything
 * from here. Same precedent as `listViewFilters.ts`.
 *
 * Null when no composer is mounted, so callers must handle its absence rather
 * than assume a ticket page is open.
 */
export const replyComposer = shallowRef<
  ((reply: RenderedSavedReply) => void) | null
>(null);
