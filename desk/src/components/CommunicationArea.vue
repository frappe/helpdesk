<template>
  <div ref="rootRef" class="comm-area">
    <!-- Minimized pill — the default state; opens the composer window. Stays
         hidden while the window's close animation plays. -->
    <div v-show="!windowOpen && !closing" ref="pillBlockRef" class="px-4 py-3">
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
        <Button variant="ghost" label="Expand" tooltip="Expand">
          <template #icon><LucideMaximize2 class="h-4 w-4" /></template>
        </Button>
      </div>
    </div>
    <Transition
      :css="false"
      @enter="onWindowEnter"
      @leave="onWindowLeave"
      @enter-cancelled="cancelWindowAnimation"
      @leave-cancelled="cancelWindowAnimation"
    >
      <div v-show="windowOpen">
        <div class="px-4 pb-3">
          <FloatingWindow
            v-model:mode="windowMode"
            :storage-key="WINDOW_STORAGE_KEY"
            class="ticket-composer-window"
            :style="composerBodyStyle"
          >
            <!-- Custom chrome: channel switcher left, window controls right.
                 The header is the resize handle while docked and the drag
                 handle while floating (the library ignores buttons). -->
            <template #header="{ mode, dock, float }">
              <div
                class="relative flex w-full items-center justify-between gap-2 p-2"
                :class="
                  mode === 'docked' && !isMobileView ? 'cursor-ns-resize' : ''
                "
                @pointerdown="onHeaderPointerDown($event, mode)"
              >
                <button
                  v-if="mode === 'docked' && !isMobileView"
                  type="button"
                  class="absolute left-1/2 top-0 z-10 flex h-4 w-24 -translate-x-1/2 cursor-ns-resize touch-none items-center justify-center rounded-full opacity-60 transition-opacity hover:opacity-100 focus:opacity-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-outline-gray-3"
                  aria-label="Resize composer"
                  @pointerdown.stop.prevent="startDockedResize"
                  @keydown.up.prevent="resizeDockedBy(16)"
                  @keydown.down.prevent="resizeDockedBy(-16)"
                >
                  <span class="h-1 w-10 rounded-full bg-surface-gray-4" />
                </button>
                <!-- The header's corners sit under the tab and window buttons,
                     so grabbing one did nothing. These zones layer over them
                     and start the same vertical resize. -->
                <span
                  v-if="mode === 'docked' && !isMobileView"
                  class="absolute left-0 top-0 z-20 size-3 cursor-ns-resize touch-none"
                  @pointerdown.stop.prevent="startDockedResize"
                />
                <span
                  v-if="mode === 'docked' && !isMobileView"
                  class="absolute right-0 top-0 z-20 size-3 cursor-ns-resize touch-none"
                  @pointerdown.stop.prevent="startDockedResize"
                />
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
                          mode === 'floating'
                            ? LucideMinimize2
                            : LucideMaximize2
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
                 so drafts survive — same semantics as the old editors. h-full
                 keeps the composer stretching to a floating window's height,
                 pinning its toolbar to the bottom. -->
            <div class="h-full" @keydown.esc.capture.stop="closeComposer">
              <EmailComposer
                v-show="
                  showEmailBox || (closing && lastOpenChannel === 'email')
                "
                ref="emailComposerRef"
                v-model="emailBody"
                v-model:recipients="recipients"
                v-model:quoted="quotedContent"
                v-model:from="fromEmail"
                :header-fields="headerFields"
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
                  <button
                    class="flex rounded p-1 text-ink-gray-8 transition-colors focus-within:ring-0 hover:bg-surface-gray-3"
                    @click="showSavedRepliesSelectorModal = true"
                  >
                    <SavedReplyIcon class="h-4 w-4" />
                  </button>
                </template>
              </EmailComposer>
              <CommentComposer
                v-show="
                  showCommentBox || (closing && lastOpenChannel === 'comment')
                "
                ref="commentComposerRef"
                v-model="commentBody"
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
          </FloatingWindow>
        </div>
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
import { showCommentBox, showEmailBox } from "@/pages/ticket/modalStates";
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
  HeaderField,
  MentionOption,
  Recipient,
  Recipients,
} from "@framework/ui/components/Composer/index.ts";
import {
  CommentComposer,
  EmailComposer,
} from "@framework/ui/components/Composer/index.ts";
import { onClickOutside, useStorage } from "@vueuse/core";
import {
  Avatar,
  TabButtons,
  createResource,
  frappeRequest,
  toast,
} from "frappe-ui";
import { FloatingWindow, type WindowMode } from "frappe-ui/experimental";
import LucideMaximize2 from "~icons/lucide/maximize-2";
import LucideMinimize2 from "~icons/lucide/minimize-2";
import LucideX from "~icons/lucide/x";
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
const emailComposerRef = ref<InstanceType<typeof EmailComposer> | null>(null);
const commentComposerRef = ref<InstanceType<typeof CommentComposer> | null>(
  null
);

// ─── Window state ─────────────────────────────────────────────
const windowOpen = computed(() => showEmailBox.value || showCommentBox.value);
const windowMode = ref<WindowMode>("docked");

// FloatingWindow persists {mode, rect}. Keep the rect, but never let it
// restore a detached mode: the composer mounts closed, and a restored
// "floating" would render an empty detached frame. Runs before the child
// reads the key.
const WINDOW_STORAGE_KEY = "helpdesk-reply-window";
try {
  const savedWindow = JSON.parse(
    localStorage.getItem(WINDOW_STORAGE_KEY) || "null"
  );
  if (savedWindow?.mode && savedWindow.mode !== "docked") {
    localStorage.setItem(
      WINDOW_STORAGE_KEY,
      JSON.stringify({ ...savedWindow, mode: "docked" })
    );
  }
} catch {
  localStorage.removeItem(WINDOW_STORAGE_KEY);
}

// ─── Open/close animation ─────────────────────────────────────
// The window morphs between the pill's height and its own natural height.
// WAAPI instead of a CSS transition: it always completes (the old
// grid-template-rows transition wedged around Teleport/fixed heights).
const pillBlockRef = ref<HTMLElement | null>(null);
const closing = ref(false);
let pillHeight = 56;
let windowAnimation: Animation | null = null;

// A hidden window must be docked: v-show can't hide a panel teleported to
// <body>, and mobile never leaves the docked state. Pre-flush, so the pill is
// still in the DOM to measure when opening — and `closing` is set before the
// same patch hides the composers, or the window collapses to a header-only
// bar before the leave animation can even measure it.
watch(
  windowOpen,
  (open, wasOpen) => {
    if (open) {
      pillHeight = pillBlockRef.value?.offsetHeight || pillHeight;
    } else {
      if (wasOpen) closing.value = true;
      windowMode.value = "docked";
    }
  },
  { immediate: true }
);

// Which composer the close animation should keep on screen.
const lastOpenChannel = ref<"email" | "comment">("email");
watch([showEmailBox, showCommentBox], ([email, comment]) => {
  if (email) lastOpenChannel.value = "email";
  else if (comment) lastOpenChannel.value = "comment";
});

function runWindowAnimation(
  el: HTMLElement,
  keyframes: Keyframe[],
  duration: number,
  done: () => void
) {
  windowAnimation?.cancel();
  el.style.overflow = "hidden";
  // fill: "forwards" holds the last keyframe past the animation's end;
  // without it the element snaps back to full height/opacity for the frame
  // between the animation finishing and Vue applying v-show — a visible
  // flash of the window chrome. The fill is released only after done().
  const animation = el.animate(keyframes, {
    duration,
    easing: "cubic-bezier(0.32, 0.72, 0, 1)",
    fill: "forwards",
  });
  windowAnimation = animation;
  const settle = () => {
    animation.onfinish = animation.oncancel = null;
    if (windowAnimation === animation) windowAnimation = null;
    closing.value = false;
    done();
    animation.cancel();
    el.style.overflow = "";
  };
  animation.onfinish = animation.oncancel = settle;
}

// The window fades while it is pill-sized: bottom-clipped small heights show
// only the header strip, which otherwise lingers as a stray chrome bar.
function onWindowEnter(el: Element, done: () => void) {
  const block = el as HTMLElement;
  runWindowAnimation(
    block,
    [
      { height: `${pillHeight}px`, opacity: 0 },
      { opacity: 1, offset: 0.4 },
      { height: `${block.offsetHeight}px`, opacity: 1 },
    ],
    250,
    done
  );
}

// Set by an overdrag-minimize; applied once the window is out of sight.
let restoreBodyHeightAfterClose: number | null = null;

function onWindowLeave(el: Element, done: () => void) {
  const block = el as HTMLElement;
  closing.value = true;
  runWindowAnimation(
    block,
    [
      { height: `${block.offsetHeight}px`, opacity: 1 },
      { height: `${pillHeight}px`, opacity: 0 },
    ],
    200,
    () => {
      if (restoreBodyHeightAfterClose !== null) {
        composerBodyHeight.value = restoreBodyHeightAfterClose;
        restoreBodyHeightAfterClose = null;
      }
      done();
    }
  );
}

function cancelWindowAnimation() {
  windowAnimation?.cancel();
}
// Covers the storage-restored "floating" mode arriving after mount while the
// window is closed — it would otherwise render an empty detached frame.
watch(windowMode, (mode) => {
  if (mode !== "docked" && (!windowOpen.value || isMobileView.value)) {
    windowMode.value = "docked";
  }
});

function toggleEmailBox() {
  if (showCommentBox.value) {
    showCommentBox.value = false;
  }
  showEmailBox.value = !showEmailBox.value;
}

function toggleCommentBox() {
  if (showEmailBox.value) {
    showEmailBox.value = false;
  }
  showCommentBox.value = !showCommentBox.value;
}

function closeComposer() {
  showEmailBox.value = false;
  showCommentBox.value = false;
}

// The window-header switcher; the two show flags stay the source of truth so
// external writers (Sidebar onboarding, mobile toggles, shortcuts) keep working.
const channelOptions = [
  { label: "Email", value: "email" },
  { label: "Comment", value: "comment" },
];

const channel = computed({
  get: () =>
    showCommentBox.value ||
    (closing.value && lastOpenChannel.value === "comment")
      ? "comment"
      : "email",
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

// Drag-set height for the docked editing area (shared by both channels, via
// the --composer-body-height CSS var in index.css); floating mode keeps the
// window's own edge resize.
const composerBodyHeight = useStorage<number | null>(
  "helpdesk-composer-height",
  null
);

// Guard every read. useStorage's null default means values rehydrate as
// strings after a reload, and a NaN that sneaks in would poison all later
// drags (NaN arithmetic no-ops silently, then persists itself).
function storedBodyHeight(): number | null {
  const value = Number(composerBodyHeight.value);
  return Number.isFinite(value) && value > 0 ? value : null;
}

const composerBodyStyle = computed(() =>
  storedBodyHeight()
    ? { "--composer-body-height": `${storedBodyHeight()}px` }
    : undefined
);

const MIN_BODY_HEIGHT = 120;
// Dragging this far below the minimum collapses the window back to the pill.
const MINIMIZE_OVERDRAG = 60;

function clampBodyHeight(value: number) {
  return Math.min(
    Math.max(value, MIN_BODY_HEIGHT),
    Math.round(window.innerHeight * 0.7)
  );
}

function resizeDockedBy(delta: number) {
  composerBodyHeight.value = clampBodyHeight(
    (storedBodyHeight() ?? 160) + delta
  );
}

// While a resize drag is live, a pointer released outside the (resized)
// window must not count as an outside click.
let suppressOutsideClose = false;

// Teardown of the live drag. A drag must never stack on another or outlive
// the component — leaked window listeners keep resizing on every mouse move.
let stopActiveResize: (() => void) | null = null;

// Anywhere on the docked header (except its buttons) starts a resize drag —
// the pill handle alone is too small a target. Floating mode falls through to
// the library's window drag.
function onHeaderPointerDown(event: PointerEvent, mode: WindowMode) {
  if (mode !== "docked" || isMobileView.value) return;
  const target = event.target as HTMLElement;
  if (target.closest("button, a, input, select, textarea, [role='button']"))
    return;
  event.preventDefault();
  startDockedResize(event);
}

function startDockedResize(event: PointerEvent) {
  stopActiveResize?.();
  const handle = event.currentTarget as HTMLElement;
  suppressOutsideClose = true;
  const body = [
    ...document.querySelectorAll<HTMLElement>(
      ".ticket-composer-window [data-slot='body']"
    ),
  ].find((el) => el.offsetParent);
  const startHeight = storedBodyHeight() ?? body?.offsetHeight ?? 160;
  const startY = event.clientY;
  try {
    handle.setPointerCapture(event.pointerId);
  } catch {}
  // Listen on window, not the handle: capture is best-effort (synthetic
  // pointers have no id) and bubbled events reach window either way.
  const onMove = (e: PointerEvent) => {
    const next = startHeight + (startY - e.clientY);
    if (next < MIN_BODY_HEIGHT - MINIMIZE_OVERDRAG) {
      // Dragged well past the floor: collapse to the pill. The pre-drag height
      // is restored only after the close animation — restoring now would grow
      // the window for one frame mid-collapse.
      stop();
      restoreBodyHeightAfterClose = clampBodyHeight(startHeight);
      closeComposer();
      return;
    }
    composerBodyHeight.value = clampBodyHeight(next);
  };
  const stop = () => {
    stopActiveResize = null;
    window.removeEventListener("pointermove", onMove);
    window.removeEventListener("pointerup", stop);
    window.removeEventListener("pointercancel", stop);
    // The click event fires after pointerup; lift the guard a task later.
    setTimeout(() => (suppressOutsideClose = false), 0);
  };
  stopActiveResize = stop;
  window.addEventListener("pointermove", onMove);
  window.addEventListener("pointerup", stop);
  window.addEventListener("pointercancel", stop);
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

const headerFields = computed<HeaderField[]>(() =>
  hasMultipleSenders.value ? ["from", "to", "cc", "bcc"] : ["to", "cc", "bcc"]
);

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

function seedRecipients(): Recipients {
  return {
    to: toRecipientList(props.toEmails),
    cc: toRecipientList(props.ccEmails),
    bcc: toRecipientList(props.bccEmails),
  };
}

const recipients = ref<Recipients>(seedRecipients());

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
    emailComposerRef.value?.reset();
    recipients.value = seedRecipients();
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
  const { to, cc, bcc } = payload.recipients;
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
  if (windowMode.value === "minimized") {
    windowMode.value = "docked";
  }

  recipients.value = {
    to: toRecipientList(splitIfString(data.to)),
    cc: toRecipientList(splitIfString(data.cc)),
    bcc: toRecipientList(splitIfString(data.bcc)),
  };

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
    // A floating or minimized window lives outside the page flow — only the
    // docked composer closes on outside clicks.
    if (windowMode.value !== "docked") return;
    if (suppressOutsideClose) return;
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
  stopActiveResize?.();
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
@media screen and (max-width: 640px) {
  .comm-area {
    width: 100vw;
  }
}
</style>
