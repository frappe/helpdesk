<template>
  <div ref="rootRef" class="max-sm:w-screen">
    <!-- Minimized pill — the default state; opens the composer window. -->
    <div v-show="!windowOpen" class="px-4 py-3">
      <div
        role="button"
        tabindex="0"
        class="flex w-full cursor-pointer items-center gap-3 rounded-lg bg-surface-elevation-2 py-1 pl-2 pr-1 text-base text-ink-gray-5 shadow-md hover:bg-surface-elevation-3 focus:outline-none focus-visible:ring-2 focus-visible:ring-outline-gray-3"
        @click="openComposer()"
        @keydown.enter.prevent="openComposer()"
        @keydown.space.prevent="openComposer()"
      >
        <Avatar :image="userImage" :label="userName" size="md" />
        <span class="min-w-0 flex-1 truncate py-1 text-left">
          {{ minimizedLabel }}
        </span>
        <TypingIndicator :ticketId="ticketId" />
        <Button
          variant="ghost"
          label="Expand"
          tooltip="Expand"
          @click.stop="openFloatingComposer"
        >
          <template #icon><LucideMaximize2 class="h-4 w-4" /></template>
        </Button>
      </div>
    </div>
    <!-- Enter classes only: closing is instant, so the composers can hide in
         the same patch without a keep-alive dance. -->
    <Transition
      enter-active-class="transition duration-150 ease-out motion-reduce:transition-none"
      enter-from-class="translate-y-1 opacity-0"
    >
      <div v-show="windowOpen" class="px-4 pb-3">
        <FloatingWindow
          v-model:mode="windowMode"
          class="ticket-composer-window"
          :class="{ 'composer-resized': dockedHeight > 0 }"
          @pointerdown="onPanelPointerDown"
        >
          <!-- Single chrome row: channel switcher left, window controls right.
               Doubles as the library's drag handle while floating and our
               resize surface while docked. -->
          <template #header="{ mode, dock, float }">
            <div
              class="flex w-full items-center justify-between gap-2 px-2.5 py-2"
            >
              <!-- Visible grab pill at the window's top edge (the panel root is
                   the positioned ancestor); also the keyboard resize handle. -->
              <button
                v-if="mode === 'docked'"
                type="button"
                class="absolute left-1/2 top-0 z-10 hidden h-6 w-24 -translate-x-1/2 cursor-ns-resize touch-none items-center justify-center rounded-full opacity-60 transition-opacity hover:opacity-100 focus:opacity-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-outline-gray-3 sm:flex"
                aria-label="Resize composer"
                @pointerdown.stop.prevent="startDockedResize($event)"
                @keydown.up.prevent="resizeDockedBy(16)"
                @keydown.down.prevent="resizeDockedBy(-16)"
              >
                <span class="h-1 w-10 rounded-full bg-surface-gray-4" />
              </button>
              <TabButtons v-model="channel" :options="channelOptions" />
              <div class="min-w-0 flex-1">
                <TypingIndicator :ticketId="ticketId" />
              </div>
              <div class="flex shrink-0 items-center gap-1">
                <Button
                  v-if="!isMobileView"
                  variant="ghost"
                  :label="mode === 'floating' ? 'Dock' : 'Pop out'"
                  :tooltip="mode === 'floating' ? 'Dock' : 'Pop out'"
                  @click="mode === 'floating' ? dock() : float()"
                >
                  <template #icon>
                    <component
                      :is="
                        mode === 'floating' ? LucideMinimize2 : LucideMaximize2
                      "
                      class="h-4 w-4"
                    />
                  </template>
                </Button>
                <Button
                  variant="ghost"
                  label="Close"
                  tooltip="Close"
                  @click="closeComposer"
                >
                  <template #icon><LucideX class="h-4 w-4" /></template>
                </Button>
              </div>
            </div>
          </template>
          <!-- Esc closes the window before the composer's internal Esc-reset,
               so drafts survive. Full-height column while floating pins the
               composer toolbar to the window bottom; a dragged docked height
               sizes the in-flow window through this column. -->
          <div
            ref="columnRef"
            class="flex min-h-0 flex-col"
            :class="windowMode === 'floating' ? 'h-full' : ''"
            :style="dockedColumnStyle"
            @keydown.esc.capture.stop="closeComposer"
          >
            <!-- v-show keeps both mounted so each draft survives a tab switch. -->
            <div
              v-show="showEmailBox"
              class="flex min-h-0 flex-1 flex-col px-2.5 py-2"
            >
              <EmailComposer
                ref="emailComposerRef"
                v-model="emailBody"
                v-model:to="to"
                v-model:cc="cc"
                v-model:bcc="bcc"
                v-model:quoted="quotedContent"
                v-model:from="fromEmail"
                class="min-h-0 flex-1"
                :show-from="hasMultipleSenders"
                :senders="senders"
                :search-recipients="searchRecipients"
                :upload-function="uploadFile"
                placeholder="Hi John, we are looking into this issue."
                :submit-label="emailSubmitLabel"
                @submit="onEmailSubmit"
                @remove-attachment="
                  (file) => removeAttachmentFromServer(file.name)
                "
              >
                <template #actions>
                  <Button
                    variant="ghost"
                    size="sm"
                    label="Saved replies"
                    tooltip="Saved replies"
                    @click="showSavedRepliesSelectorModal = true"
                  >
                    <template #icon
                      ><SavedReplyIcon class="h-4 w-4"
                    /></template>
                  </Button>
                </template>
              </EmailComposer>
            </div>
            <div
              v-show="showCommentBox"
              class="flex min-h-0 flex-1 flex-col px-2.5 py-2"
            >
              <CommentComposer
                ref="commentComposerRef"
                v-model="commentBody"
                class="min-h-0 flex-1"
                :mentions="mentionOptions"
                :upload-function="uploadFile"
                placeholder="@John could you please look into this?"
                :submit-label="commentSubmitLabel"
                @submit="onCommentSubmit"
                @remove-attachment="
                  (file) => removeAttachmentFromServer(file.name)
                "
              />
            </div>
          </div>
        </FloatingWindow>
      </div>
    </Transition>
  </div>
  <SavedRepliesSelectorModal
    v-model="showSavedRepliesSelectorModal"
    :doctype="doctype"
    :ticketId="ticketId"
    @apply="applySavedReply"
  />
</template>

<script setup lang="ts">
import { SavedRepliesSelectorModal, TypingIndicator } from "@/components";
import { useDevice } from "@/composables";
import { useTyping } from "@/composables/realtime";
import { useScreenSize } from "@/composables/screen";
import { useShortcut } from "@/composables/shortcuts";
import { getUserEmailInfo } from "@/composables/useUserEmailInfo";
import {
  showCommentBox,
  showEmailBox,
  toggleCommentBox,
  toggleEmailBox,
} from "@/pages/ticket/modalStates";
import { useAgentStore } from "@/stores/agent";
import { useAuthStore } from "@/stores/auth";
import {
  htmlToText,
  isContentEmpty,
  removeAttachmentFromServer,
  uploadFunction,
} from "@/utils";
// Deep import: the @framework/ui root barrel would pull the whole library
// (FormLayout, ListView, …) into the bundle — same pattern as TicketField's
// Link import.
import type {
  CommentPayload,
  EmailPayload,
  MentionOption,
  Recipient,
} from "@framework/ui/components/Composer/index.ts";
import {
  CommentComposer,
  EmailComposer,
} from "@framework/ui/components/Composer/index.ts";
import { onClickOutside, useEventListener, useStorage } from "@vueuse/core";
import {
  Avatar,
  TabButtons,
  createResource,
  frappeRequest,
  toast,
} from "frappe-ui";
import { FloatingWindow, type WindowMode } from "frappe-ui/experimental";
import { useOnboarding } from "frappe-ui/frappe";
import { storeToRefs } from "pinia";
import {
  computed,
  nextTick,
  onBeforeUnmount,
  onMounted,
  ref,
  watch,
} from "vue";
import LucideMaximize2 from "~icons/lucide/maximize-2";
import LucideMinimize2 from "~icons/lucide/minimize-2";
import LucideX from "~icons/lucide/x";
import SavedReplyIcon from "./icons/SavedReplyIcon.vue";

const props = defineProps({
  doctype: {
    type: String,
    default: "HD Ticket",
  },
  ticketId: {
    type: String,
    default: null,
  },
  toEmails: {
    type: Array,
    default: () => [],
  },
  ccEmails: {
    type: Array,
    default: () => [],
  },
  bccEmails: {
    type: Array,
    default: () => [],
  },
});

const emit = defineEmits(["update"]);
// MobileTicketAgent binds v-model="ticket.doc"; keep the model registered.
const doc = defineModel();

const { isMac } = useDevice();
const { isMobileView } = useScreenSize();
const { updateOnboardingStep } = useOnboarding("helpdesk");
const { isManager, userImage, userName } = useAuthStore();
const { onUserType, cleanup } = useTyping(props.ticketId);

const rootRef = ref(null);
const columnRef = ref<HTMLElement | null>(null);
const emailComposerRef = ref<InstanceType<typeof EmailComposer> | null>(null);
const commentComposerRef = ref<InstanceType<typeof CommentComposer> | null>(
  null
);

// ─── Window state ─────────────────────────────────────────────
const windowOpen = computed(() => showEmailBox.value || showCommentBox.value);
const windowMode = ref<WindowMode>("docked");

// A non-docked panel teleports to <body>, so the wrapper's v-show can't hide
// it: force docked whenever the window is closed or the viewport is mobile.
watch([windowOpen, isMobileView, windowMode], ([open, mobile, mode]) => {
  if (mode !== "docked" && (!open || mobile)) {
    windowMode.value = "docked";
  }
});

function closeComposer() {
  showEmailBox.value = false;
  showCommentBox.value = false;
}

// ─── Channel & pill ───────────────────────────────────────────
// The two show flags stay the source of truth so external writers (Sidebar
// onboarding, mobile toggles, shortcuts) keep working.
const channelOptions = [
  { label: "Email", value: "email" },
  { label: "Comment", value: "comment" },
];

const channel = computed({
  get: () => (showCommentBox.value ? "comment" : "email"),
  set: (value) => {
    showEmailBox.value = value === "email";
    showCommentBox.value = value === "comment";
  },
});

const hasEmailDraft = computed(
  () =>
    (!isContentEmpty(emailBody.value) && !isOnlySignature(emailBody.value)) ||
    !!quotedContent.value
);
const hasCommentDraft = computed(() => !isContentEmpty(commentBody.value));

function openComposer() {
  if (hasCommentDraft.value && !hasEmailDraft.value) {
    showCommentBox.value = true;
    showEmailBox.value = false;
    return;
  }
  showEmailBox.value = true;
  showCommentBox.value = false;
}

// The pill's expand button skips the docked stage and pops straight out
// (the mode watcher forces docked back on mobile, where it just opens).
function openFloatingComposer() {
  openComposer();
  windowMode.value = "floating";
}

const minimizedLabel = computed(() => {
  let draft: string | null = null;
  if (hasEmailDraft.value) {
    // Quoted-only drafts (reply started, nothing typed) preview the quote.
    draft =
      !isContentEmpty(emailBody.value) && !isOnlySignature(emailBody.value)
        ? emailBody.value
        : quotedContent.value;
  } else if (hasCommentDraft.value) {
    draft = commentBody.value;
  }
  const preview = draft ? htmlToText(draft).trim() : "";
  return preview || "Send a reply";
});

// ─── Docked-height resize ─────────────────────────────────────
// Dragging the title bar sizes the in-flow window by setting an explicit
// height on our body column — no library hook needed. 0 means natural height.
// The number default keeps useStorage on the number serializer, so reloads
// can't rehydrate the value as a string.
const dockedHeight = useStorage("helpdesk-composer-height", 0);

const MIN_BODY_HEIGHT = 240;
// Dragging this far below the minimum collapses the window back to the pill.
const MINIMIZE_OVERDRAG = 60;

const dockedColumnStyle = computed(() =>
  windowMode.value === "docked" && dockedHeight.value > 0
    ? { height: `${dockedHeight.value}px` }
    : undefined
);

function clampBodyHeight(value: number) {
  return Math.min(
    Math.max(value, MIN_BODY_HEIGHT),
    Math.round(window.innerHeight * 0.8)
  );
}

// The live drag; move/up listeners are registered once below and no-op while
// this is null, so nothing can stack or leak.
let resizing: { startY: number; startHeight: number } | null = null;
// A pointer released outside the window must not count as an outside click.
let justResized = false;

// Bound on <FloatingWindow>, so it lands on the panel root and catches
// pointerdowns bubbling from the built-in title bar. The column containment
// test limits the resize surface to the chrome without naming its internals;
// the button filter matches the library's own drag bail-out.
function onPanelPointerDown(event: PointerEvent) {
  if (windowMode.value !== "docked" || isMobileView.value) return;
  const target = event.target as HTMLElement;
  if (target.closest("button, a, input, select, textarea, [role='button']"))
    return;
  if (columnRef.value?.contains(target)) return;
  event.preventDefault();
  startDockedResize(event);
}

function startDockedResize(event: PointerEvent) {
  resizing = {
    startY: event.clientY,
    startHeight: currentBodyHeight(),
  };
  // Best-effort: a successful capture keeps the post-drag click inside the
  // panel; synthetic pointers without an id fall back to the guard flag.
  try {
    (event.currentTarget as HTMLElement).setPointerCapture(event.pointerId);
  } catch {}
}

function currentBodyHeight() {
  return dockedHeight.value || columnRef.value?.offsetHeight || MIN_BODY_HEIGHT;
}

function resizeDockedBy(delta: number) {
  dockedHeight.value = clampBodyHeight(currentBodyHeight() + delta);
}

useEventListener(window, "pointermove", (event: PointerEvent) => {
  if (!resizing) return;
  const next = resizing.startHeight + (resizing.startY - event.clientY);
  if (next < MIN_BODY_HEIGHT - MINIMIZE_OVERDRAG) {
    // Dragged well past the floor: collapse to the pill, keeping the pre-drag
    // height so reopening restores it.
    const previous = resizing.startHeight;
    stopDockedResize();
    dockedHeight.value = clampBodyHeight(previous);
    closeComposer();
    return;
  }
  dockedHeight.value = clampBodyHeight(next);
});
useEventListener(window, "pointerup", stopDockedResize);
useEventListener(window, "pointercancel", stopDockedResize);

function stopDockedResize() {
  if (!resizing) return;
  resizing = null;
  justResized = true;
  // The click event fires after pointerup; lift the guard a task later.
  setTimeout(() => (justResized = false), 0);
}

// ─── Email draft & signature ──────────────────────────────────
const cachedEmail = useStorage<string | null>(
  "emailBoxContent" + props.ticketId,
  null
);
const emailBody = ref<string>(cachedEmail.value ?? "");
const quotedContent = useStorage<string | null>(
  "quotedEmailBoxContent" + props.ticketId,
  null
);
const emailSignature = ref<string | null>(null);

function isOnlySignature(content: string | null) {
  if (!content || !emailSignature.value) return false;
  return htmlToText(content) === htmlToText(emailSignature.value);
}

const userResource = getUserEmailInfo();

watch(
  () => userResource.data,
  (data: { email_signature?: string } | null) => {
    if (!data?.email_signature) return;
    emailSignature.value = `<br>${data.email_signature}`;
    if (isOnlySignature(cachedEmail.value)) {
      cachedEmail.value = null;
    }
    if (isContentEmpty(emailBody.value) && !quotedContent.value) {
      emailBody.value = emailSignature.value;
    }
  },
  { immediate: true }
);

watch(emailBody, (value, oldValue) => {
  if (value !== oldValue && value) {
    onUserType();
  }
  cachedEmail.value = isOnlySignature(value) ? null : value || null;
});

// ─── Sender identities ────────────────────────────────────────
const fromEmail = useStorage<string>("from-email", "");

const outgoingEmails = computed<{ email_account: string; email_id: string }[]>(
  () => userResource.data?.outgoing_emails ?? []
);

const senders = computed<Recipient[]>(() => {
  if (!outgoingEmails.value.length) return [];
  if (
    outgoingEmails.value.length === 1 &&
    outgoingEmails.value[0].email_id === userResource.data?.email
  )
    return [];
  return outgoingEmails.value.map((e) => ({
    label: e.email_account + " <" + e.email_id + ">",
    email: e.email_id,
  }));
});

const hasMultipleSenders = computed(() => senders.value.length > 1);

watch(
  senders,
  (options) => {
    if (!options.find((option) => option.email === fromEmail.value)) {
      fromEmail.value = options.length ? options[0].email : "";
    }
  },
  { immediate: true }
);

// ─── Recipients ───────────────────────────────────────────────
function toRecipientList(emails: unknown[] | undefined): Recipient[] {
  return (emails ?? []).filter(Boolean).map((email) => ({
    email: String(email),
  }));
}

const to = ref<Recipient[]>([]);
const cc = ref<Recipient[]>([]);
const bcc = ref<Recipient[]>([]);

function resetRecipients() {
  to.value = toRecipientList(props.toEmails);
  cc.value = toRecipientList(props.ccEmails);
  bcc.value = toRecipientList(props.bccEmails);
}
resetRecipients();

// Plain request, not createResource: RecipientSelect evaluates this inside a
// computedAsync, and touching a reactive resource there re-triggers evaluation
// forever.
async function searchRecipients(query: string): Promise<Recipient[]> {
  const contacts = await frappeRequest<
    { full_name?: string; name: string; email_id: string }[]
  >({
    url: "/api/method/helpdesk.api.contact.search_contacts",
    method: "GET",
    params: { txt: query },
  });
  return (contacts ?? []).map(
    (contact: { full_name?: string; name: string; email_id: string }) => ({
      email: contact.email_id,
      label: contact.full_name || contact.name || contact.email_id,
    })
  );
}

// ─── Attachments ──────────────────────────────────────────────
function uploadFile(file: File) {
  return uploadFunction(file, props.doctype, props.ticketId);
}

// ─── Saved replies ────────────────────────────────────────────
const showSavedRepliesSelectorModal = ref(false);

function applySavedReply(template: string) {
  const editor = emailComposerRef.value?.editor;
  if (!editor) return;
  editor.chain().focus("start").insertContent(template).run();
}

// ─── Send email ───────────────────────────────────────────────
const sendMail = createResource({
  url: "run_doc_method",
  debounce: 300,
  onSuccess: () => {
    // reset() clears the to/cc/bcc models itself, so re-seed after it.
    emailComposerRef.value?.reset();
    resetRecipients();
    emailBody.value = emailSignature.value ?? "";
    showEmailBox.value = false;
    emit("update");
    if (isManager) {
      updateOnboardingStep("reply_on_ticket");
    }
  },
});

const emailSubmitLabel = computed(() => {
  if (sendMail.loading) return "Sending...";
  return isMobileView.value
    ? "Send"
    : isMac
    ? "Send (⌘ + ⏎)"
    : "Send (Ctrl + ⏎)";
});

function onEmailSubmit(payload: EmailPayload) {
  if (sendMail.loading) return;
  const { to, cc, bcc } = payload;
  if (!to.length && !cc.length && !bcc.length) {
    toast.warning(
      "Email has no recipients. Please add at least one recipient (To, Cc, or Bcc) before sending."
    );
    return;
  }
  // The composer already appended the quoted block to `body` in the exact
  // wire format reply_via_agent expects; a failed send leaves the draft
  // untouched because nothing is cleared until onSuccess.
  sendMail.submit({
    dt: props.doctype,
    dn: props.ticketId,
    method: "reply_via_agent",
    args: {
      attachments: payload.attachments.map((file) => file.name),
      from_email: outgoingEmails.value.find((e) => e.email_id === payload.from),
      to: to.map((recipient) => recipient.email).join(","),
      cc: cc.map((recipient) => recipient.email).join(","),
      bcc: bcc.map((recipient) => recipient.email).join(","),
      message: payload.body,
    },
  });
}

// ─── Comment ──────────────────────────────────────────────────
const commentBody = useStorage<string | null>(
  "commentBoxContent" + props.ticketId,
  null
);

const { agents: agentsList, dropdown } = storeToRefs(useAgentStore());
const mentionOptions = computed<MentionOption[]>(() => dropdown.value ?? []);

const sendComment = createResource({
  url: "run_doc_method",
  onSuccess: () => {
    commentComposerRef.value?.reset();
    showCommentBox.value = false;
    emit("update");
    if (isManager) {
      updateOnboardingStep("comment_on_ticket");
    }
  },
});

const commentSubmitLabel = computed(() => {
  if (sendComment.loading) return "Commenting...";
  return isMobileView.value
    ? "Comment"
    : isMac
    ? "Comment (⌘ + ⏎)"
    : "Comment (Ctrl + ⏎)";
});

function onCommentSubmit(payload: CommentPayload) {
  if (sendComment.loading) return;
  sendComment.submit({
    dt: props.doctype,
    dn: props.ticketId,
    method: "new_comment",
    args: {
      content: payload.body,
      attachments: payload.attachments,
    },
  });
}

watch(commentBody, (value, oldValue) => {
  if (value !== oldValue && value) {
    onUserType();
  }
});

// ─── Reply from the activity feed ─────────────────────────────
function splitIfString(value: string | string[]) {
  if (typeof value === "string") {
    return value.split(",");
  }
  return value;
}

function replyToEmail(data: {
  content: string;
  to: string | string[];
  cc: string | string[];
  bcc: string | string[];
}) {
  showCommentBox.value = false;
  showEmailBox.value = true;

  to.value = toRecipientList(splitIfString(data.to));
  cc.value = toRecipientList(splitIfString(data.cc));
  bcc.value = toRecipientList(splitIfString(data.bcc));

  // Plain-text emails (e.g. Thunderbird) have no HTML tags, so their
  // newlines/spacing would be lost in the quoted block.
  let body = data.content;
  const parsed = new DOMParser().parseFromString(body, "text/html");
  if (parsed.body.children.length === 0) {
    body = `<div style="white-space: pre-wrap; line-height: 1.5">${parsed.body.innerHTML}</div>`;
  }
  quotedContent.value = body;

  nextTick(() => {
    emailBody.value = emailSignature.value ?? "";
    emailComposerRef.value?.focus();
  });
}

// ─── Open/close behavior ──────────────────────────────────────
watch(showEmailBox, (open) => {
  if (open) nextTick(() => emailComposerRef.value?.focus());
});

watch(showCommentBox, (open) => {
  if (open) nextTick(() => commentComposerRef.value?.focus());
});

useShortcut("r", () => {
  toggleEmailBox();
});
useShortcut("c", () => {
  toggleCommentBox();
});

const IGNORED_SELECTORS = [
  ".PopoverContent",
  '[role="dialog"]',
  '[role="menu"]',
  ".dialog-overlay",
  "[data-reka-popper-content-wrapper]",
];

onClickOutside(
  rootRef,
  () => {
    // A floating window lives outside the page flow — only the docked
    // composer closes on outside clicks.
    if (windowMode.value !== "docked") return;
    if (justResized) return;
    closeComposer();
  },
  {
    ignore: IGNORED_SELECTORS,
  }
);

onMounted(() => {
  if (
    agentsList.value.loading ||
    agentsList.value.data?.length ||
    agentsList.value.list.promise
  ) {
    return;
  }
  agentsList.value.fetch();
});

onBeforeUnmount(() => {
  cleanup();
  if (isContentEmpty(commentBody.value)) {
    localStorage.removeItem("commentBoxContent" + props.ticketId);
  }
});

defineExpose({
  replyToEmail,
  toggleEmailBox,
  toggleCommentBox,
});
</script>

<style>
/* When the window's height is fixed (floating, or docked at a dragged height),
   release the editor's internal 50vh cap so it fills and the toolbar pins to
   the bottom. `.overflow-y-auto` matches exactly one element inside the
   window: ComposerEditor's scroll region. */
.ticket-composer-window[data-state="floating"] .overflow-y-auto,
.ticket-composer-window.composer-resized[data-state="docked"] .overflow-y-auto {
  max-height: none;
}

/* The built-in title bar doubles as the docked resize surface. Positional
   selector into the library chrome; worst case on a library change is a wrong
   cursor, nothing functional. */
@media (min-width: 640px) {
  .ticket-composer-window[data-state="docked"] > div:first-child {
    cursor: ns-resize;
  }
}
</style>
