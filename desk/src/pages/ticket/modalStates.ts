import { RenderedSavedReply } from "@/types";
import { ref, shallowRef } from "vue";

export const showAssignmentModal = ref(false);
export const showEmailBox = ref(false);
export const showCommentBox = ref(false);
// Shared, not local to TicketHeader: the command palette opens it too.
export const showMergeModal = ref(false);
export function toggleEmailBox() {
  if (showCommentBox.value) {
    showCommentBox.value = false;
  }
  showEmailBox.value = !showEmailBox.value;
}
export function toggleCommentBox() {
  if (showEmailBox.value) {
    showEmailBox.value = false;
  }
  showCommentBox.value = !showCommentBox.value;
}

// The mounted composer's insert action, for the command palette which sits
// outside this provide chain. Null when no composer is mounted.
export const replyComposer = shallowRef<
  ((reply: RenderedSavedReply) => void) | null
>(null);
