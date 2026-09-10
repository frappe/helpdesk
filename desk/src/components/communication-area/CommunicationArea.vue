<template>
  <div ref="rootRef" class="max-sm:w-screen">
    <!-- Minimized pill — the default state; opens the composer window. -->
    <div v-show="!windowOpen" class="flex items-center gap-2 px-4 py-3">
      <div
        ref="pillRef"
        role="button"
        tabindex="0"
        class="flex w-full min-w-0 cursor-pointer items-center gap-3 rounded-lg bg-surface-elevation-2 py-1 pl-2 pr-1 text-base text-ink-gray-5 shadow-md hover:bg-surface-elevation-3 focus:outline-none focus-visible:ring-2 focus-visible:ring-outline-gray-3"
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
          class="group hover:bg-transparent active:bg-transparent"
          :label="__('Expand')"
          :tooltip="__('Expand')"
          @click.stop="openFloatingComposer"
        >
          <template #icon>
            <LucideMaximize2
              class="size-4 text-ink-gray-5 group-hover:text-ink-gray-8"
            />
          </template>
        </Button>
      </div>
      <div
        class="flex shrink-0 rounded-lg bg-surface-elevation-2 p-1 shadow-md"
      >
        <Button
          variant="ghost"
          class="group hover:bg-transparent active:bg-transparent"
          :label="channels[otherChannel].label"
          :tooltip="channels[otherChannel].label"
          @click="channel = otherChannel"
        >
          <template #icon>
            <component
              :is="channels[otherChannel].icon"
              class="size-4 text-ink-gray-5 group-hover:text-ink-gray-8"
            />
          </template>
        </Button>
      </div>
    </div>
    <!-- Enter classes only. Vue keeps a leaving element on screen for two
         frames even with no leave animation, and the pill above shows at once,
         so both stacked and then jumped. Finishing the leave synchronously
         hides the window in the same patch as the pill. -->
    <Transition
      enter-active-class="transition duration-150 ease-out motion-reduce:transition-none"
      enter-from-class="translate-y-1 opacity-0"
      @leave="(_, done) => done()"
    >
      <div v-show="windowOpen" class="px-4 pb-3">
        <FloatingWindow
          v-model:mode="windowMode"
          class="ticket-composer-window"
          :class="{ 'composer-resized': dockedHeight > 0 }"
          @pointerdown="onPanelPointerDown"
        >
          <!-- header area having switcher and actions left and right respectively -->
          <template #header="{ mode, dock, float }">
            <div
              class="flex w-full items-center justify-between gap-2 px-2.5 py-2"
              :class="mode === 'docked' ? 'sm:cursor-ns-resize' : ''"
            >
              <!-- handle to resize in docked state -->
              <div
                v-if="mode === 'docked'"
                role="separator"
                aria-orientation="horizontal"
                tabindex="0"
                class="absolute left-1/2 top-0 z-10 hidden h-6 w-24 -translate-x-1/2 cursor-ns-resize touch-none items-center justify-center rounded-full opacity-60 transition-opacity hover:opacity-100 focus:opacity-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-outline-gray-3 sm:flex"
                :aria-label="__('Resize composer')"
                @pointerdown.stop.prevent="startDockedResize($event)"
                @keydown.up.prevent="resizeDockedBy(16)"
                @keydown.down.prevent="resizeDockedBy(-16)"
              >
                <span class="h-1 w-10 rounded-full bg-surface-gray-4" />
              </div>
              <TabButtons v-model="channel" :options="channelOptions" />
              <div class="min-w-0 flex-1">
                <TypingIndicator :ticketId="ticketId" />
              </div>
              <div class="flex shrink-0 items-center gap-1">
                <Button
                  v-if="!isMobileView"
                  variant="ghost"
                  :label="mode === 'floating' ? __('Dock') : __('Pop out')"
                  :tooltip="mode === 'floating' ? __('Dock') : __('Pop out')"
                  @click="mode === 'floating' ? dock() : float()"
                >
                  <template #icon>
                    <component
                      :is="
                        mode === 'floating' ? LucideMinimize2 : LucideMaximize2
                      "
                      class="size-4"
                    />
                  </template>
                </Button>
                <Button
                  variant="ghost"
                  :label="__('Close')"
                  :tooltip="__('Close')"
                  @click="collapseToPill"
                >
                  <template #icon><LucideX class="size-4" /></template>
                </Button>
              </div>
            </div>
          </template>
          <!-- Esc button and close button minmize and put composer in dockd state-->
          <div
            ref="columnRef"
            class="flex min-h-0 flex-col"
            :class="windowMode === 'floating' ? 'h-full' : ''"
            :style="dockedColumnStyle"
            @keydown.esc.capture.stop="collapseToPill"
          >
            <div
              v-show="showEmailBox"
              class="flex min-h-0 flex-1 flex-col ps-2.5 py-2"
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
                :extensions="helpdeskExtensions"
                :placeholder="__('Hi John, we are looking into this issue.')"
                :submit-label="emailSubmitLabel"
                :submitting="sendMail.loading"
                @submit="onEmailSubmit"
                @remove-attachment="
                  (file) => removeAttachmentFromServer(file.name)
                "
              >
                <template #actions>
                  <Button
                    variant="ghost"
                    size="sm"
                    :label="__('Saved replies')"
                    :tooltip="__('Saved replies')"
                    @click="showSavedRepliesSelectorModal = true"
                  >
                    <template #icon><ZapIcon class="size-4" /></template>
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    :icon="ClearFormatting.icon"
                    :label="__('Clear formatting')"
                    :tooltip="__('Clear formatting')"
                    @click="clearFormatting(emailComposerRef?.editor)"
                  />
                </template>
                <!-- Saved reply actions, applied once the reply is sent -->
                <template #footer>
                  <SavedReplyActions
                    ref="savedReplyActionsRef"
                    class="mx-2.5 mb-2"
                    :ticket-id="ticketId"
                    :doctype="doctype"
                  />
                </template>
              </EmailComposer>
            </div>
            <div
              v-show="showCommentBox"
              class="flex min-h-0 flex-1 flex-col ps-2.5 py-2"
            >
              <CommentComposer
                ref="commentComposerRef"
                v-model="commentBody"
                class="min-h-0 flex-1"
                :mentions="mentionOptions"
                :upload-function="uploadFile"
                :extensions="helpdeskExtensions"
                :placeholder="__('@John could you please look into this?')"
                :submit-label="commentSubmitLabel"
                :submitting="sendComment.loading"
                @submit="onCommentSubmit"
                @remove-attachment="
                  (file) => removeAttachmentFromServer(file.name)
                "
              >
                <template #actions>
                  <Button
                    variant="ghost"
                    size="sm"
                    :icon="ClearFormatting.icon"
                    :label="__('Clear formatting')"
                    :tooltip="__('Clear formatting')"
                    @click="clearFormatting(commentComposerRef?.editor)"
                  />
                </template>
              </CommentComposer>
            </div>
          </div>
        </FloatingWindow>
      </div>
    </Transition>
    <SavedRepliesSelectorModal
      v-model="showSavedRepliesSelectorModal"
      :doctype="doctype"
      :ticketId="ticketId"
      @apply="applySavedReplies"
    />
  </div>
</template>

<script setup lang="ts">
import { SavedRepliesSelectorModal, TypingIndicator } from "@/components";
import { createDialog } from "@/components/dialogs";
import { CommentIcon, EmailIcon } from "@/components/icons";
import {
  ClearFormatting,
  helpdeskExtensions,
} from "@/components/editor/config";
import SavedReplyActions from "@/components/SavedReplyActions/SavedReplyActions.vue";
import { useDevice } from "@/composables";
import { useTyping } from "@/composables/realtime";
import { useScreenSize } from "@/composables/screen";
import { useShortcut } from "@/composables/shortcuts";
import { getUserEmailInfo } from "@/composables/useUserEmailInfo";
import {
  replyComposer,
  showCommentBox,
  showEmailBox,
  toggleCommentBox,
  toggleEmailBox,
} from "@/pages/ticket/modalStates";
import { useAgentStore } from "@/stores/agent";
import { useAuthStore } from "@/stores/auth";
import { capture } from "@/telemetry";
import { __ } from "@/translation";
import { RenderedSavedReply, ReplyPayload } from "@/types";
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
import { onClickOutside, useStorage } from "@vueuse/core";
import { Avatar, TabButtons, createResource, toast } from "frappe-ui";
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
import ZapIcon from "~icons/lucide/zap";
import {
  nameRecipients,
  searchRecipients,
  toRecipientList,
} from "./recipients";
import { useDockedResize } from "./useDockedResize";

const props = withDefaults(
  defineProps<{
    ticketId: string;
    doctype?: string;
    toEmails?: (string | undefined)[];
  }>(),
  { doctype: "HD Ticket", toEmails: () => [] }
);

const emit = defineEmits(["update"]);

const { isMac } = useDevice();
const { isMobileView } = useScreenSize();
const { updateOnboardingStep } = useOnboarding("helpdesk");
const { isManager, userImage, userName } = useAuthStore();
const { onUserType, cleanup } = useTyping(props.ticketId);

const rootRef = ref(null);
const pillRef = ref<HTMLElement | null>(null);
const columnRef = ref<HTMLElement | null>(null);
const emailComposerRef = ref<InstanceType<typeof EmailComposer> | null>(null);
const commentComposerRef = ref<InstanceType<typeof CommentComposer> | null>(
  null
);
const savedReplyActionsRef = ref<InstanceType<typeof SavedReplyActions>>();

// ─── Drafts & signature ──────────────────────────────────────
// Declared first: the channel table and the pill read these.
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
const commentBody = useStorage<string | null>(
  "commentBoxContent" + props.ticketId,
  null
);

function isOnlySignature(content: string | null) {
  if (!content || !emailSignature.value) return false;
  return htmlToText(content) === htmlToText(emailSignature.value);
}

const hasTypedEmail = computed(
  () => !isContentEmpty(emailBody.value) && !isOnlySignature(emailBody.value)
);
const hasEmailDraft = computed(
  () => hasTypedEmail.value || !!quotedContent.value
);
const hasCommentDraft = computed(() => !isContentEmpty(commentBody.value));

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
  // The signature drops into an empty editor on load and on every reply. That
  // is not the agent typing, and broadcasting it would show a typing indicator
  // to everyone else on the ticket.
  if (value !== oldValue && hasTypedEmail.value) {
    onUserType();
  }

  if (!value) {
    savedReplyActionsRef.value?.clear();
  }
  cachedEmail.value = isOnlySignature(value) ? null : value || null;
});

watch(commentBody, (value, oldValue) => {
  if (value !== oldValue && value) {
    onUserType();
  }
});

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

// Esc and Close hand focus to the pill. An open recipient list is rendered
// outside the hidden window and only dismisses once focus lands elsewhere.
function collapseToPill() {
  closeComposer();
  nextTick(() => pillRef.value?.focus());
}

// ─── Channel & pill ───────────────────────────────────────────
type Channel = "email" | "comment";

const channels = {
  email: {
    box: showEmailBox,
    label: __("Email"),
    icon: EmailIcon,
    composer: emailComposerRef,
    hasDraft: hasEmailDraft,
  },
  comment: {
    box: showCommentBox,
    label: __("Comment"),
    icon: CommentIcon,
    composer: commentComposerRef,
    hasDraft: hasCommentDraft,
  },
};

const channelOptions = (Object.keys(channels) as Channel[]).map((value) => ({
  label: channels[value].label,
  value,
}));

const channel = computed({
  get: (): Channel => (showCommentBox.value ? "comment" : "email"),
  set: (value: Channel) => {
    showEmailBox.value = value === "email";
    showCommentBox.value = value === "comment";
  },
});

function otherOf(name: Channel): Channel {
  return name === "email" ? "comment" : "email";
}

// The channel the agent last had open, kept per ticket like the drafts.
const lastChannel = useStorage<Channel>(
  "composerChannel" + props.ticketId,
  "email"
);

// Opening a channel records it and focuses its composer.
for (const [name, { box, composer }] of Object.entries(channels)) {
  watch(box, (open) => {
    if (!open) return;
    lastChannel.value = name as Channel;
    nextTick(() => composer.value?.focus());
  });
}

// Reopen where the agent left off, unless only the other channel holds a draft.
const nextChannel = computed<Channel>(() => {
  const last = lastChannel.value;
  const other = otherOf(last);
  return !channels[last].hasDraft.value && channels[other].hasDraft.value
    ? other
    : last;
});
const otherChannel = computed(() => otherOf(nextChannel.value));

function openComposer() {
  channel.value = nextChannel.value;
}

// Pops straight out; an already open window keeps its channel.
function openFloatingComposer() {
  if (!windowOpen.value) openComposer();
  windowMode.value = "floating";
}

const minimizedLabel = computed(() => {
  let draft: string | null = null;
  if (nextChannel.value === "comment") {
    draft = commentBody.value;
  } else if (hasEmailDraft.value) {
    // Quoted-only drafts (reply started, nothing typed) preview the quote.
    draft = hasTypedEmail.value ? emailBody.value : quotedContent.value;
  }
  const preview = draft ? htmlToText(draft).trim() : "";
  return preview || __("Send a reply");
});

// ─── Docked-height resize ─────────────────────────────────────
const {
  dockedHeight,
  dockedColumnStyle,
  justResized,
  onPanelPointerDown,
  startDockedResize,
  resizeDockedBy,
} = useDockedResize({
  windowMode,
  column: columnRef,
  isMobileView,
  onCollapse: closeComposer,
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
const to = ref<Recipient[]>([]);
const cc = ref<Recipient[]>([]);
const bcc = ref<Recipient[]>([]);

// ─── Extensions ───────────────────────────────────────────────

function clearFormatting(
  editor?: Parameters<typeof ClearFormatting.action>[0]
) {
  if (editor) ClearFormatting.action(editor);
}

// ─── Attachments ──────────────────────────────────────────────
function uploadFile(file: File) {
  return uploadFunction(file, props.doctype, props.ticketId);
}

// ─── Saved replies ────────────────────────────────────────────
const showSavedRepliesSelectorModal = ref(false);

/** A reply is only replaced when another one is already applied. */
function applySavedReplies(reply: RenderedSavedReply) {
  const staged = savedReplyActionsRef.value?.stagedSummary();
  if (!staged) {
    insertSavedReply(reply);
    return;
  }
  createDialog({
    title: __("Replace saved reply"),
    message: __(
      'Applying "{0}" discards the reply you have now, along with its {1} action(s).',
      [reply.title, staged.count]
    ),
    actions: [
      { label: __("Cancel") },
      {
        label: __("Replace"),
        variant: "solid",
        onClick: ({ close }: { close: () => void }) => {
          replaceSavedReply(reply);
          close();
        },
      },
    ],
  });
}

/** First reply of a draft: added to whatever the agent has already written. */
function insertSavedReply(reply: RenderedSavedReply) {
  const editor = emailComposerRef.value?.editor;
  if (!editor) return;
  editor.chain().focus("start").insertContent(reply.message).run();
  savedReplyActionsRef.value?.add(reply);
}

/** Confirmed replace: the new reply's body and actions stand alone. */
function replaceSavedReply(reply: RenderedSavedReply) {
  emailBody.value = reply.message + (emailSignature.value ?? "");
  savedReplyActionsRef.value?.add(reply);
  nextTick(() => emailComposerRef.value?.focus());
}

// ─── Email Helpers ───────────────────────────────────────────────
const sendMail = createResource({
  url: "run_doc_method",
  debounce: 300,
  onSuccess: () => {
    savedReplyActionsRef.value?.submit();
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

function resetRecipients() {
  to.value = toRecipientList(props.toEmails);
  cc.value = [];
  bcc.value = [];
  nameRecipients(to);
}
resetRecipients();

function replyToEmail(data: ReplyPayload) {
  showCommentBox.value = false;
  showEmailBox.value = true;

  to.value = toRecipientList(data.to);
  cc.value = toRecipientList(data.cc);
  bcc.value = toRecipientList(data.bcc);
  nameRecipients(to, cc, bcc);

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

// ─── Comment Helpers ──────────────────────────────────────────────────
const agentStore = useAgentStore();
const { dropdown } = storeToRefs(agentStore);
const mentionOptions = computed<MentionOption[]>(() => dropdown.value ?? []);

const sendComment = createResource({
  url: "run_doc_method",
  onSuccess: () => {
    capture("comment_added");
    commentComposerRef.value?.reset();
    showCommentBox.value = false;
    emit("update");
    if (isManager) {
      updateOnboardingStep("comment_on_ticket");
    }
  },
});

// ─── Sending ──────────────────────────────────────────────────
// Short on mobile, shortcut hint on desktop, the progressive form while busy.
function submitLabel(verb: string, busy: string, loading: boolean) {
  if (loading) return busy;
  if (isMobileView.value) return verb;
  return isMac ? `${verb} (⌘ + ⏎)` : `${verb} (Ctrl + ⏎)`;
}

const emailSubmitLabel = computed(() =>
  submitLabel(__("Send"), __("Sending"), sendMail.loading)
);

const commentSubmitLabel = computed(() =>
  submitLabel(__("Comment"), __("Commenting"), sendComment.loading)
);

function onEmailSubmit(payload: EmailPayload) {
  if (sendMail.loading) return;
  const { to, cc, bcc } = payload;
  if (!to.length && !cc.length && !bcc.length) {
    toast.warning(
      __(
        "Email has no recipients. Please add at least one recipient (To, Cc, or Bcc) before sending."
      )
    );
    return;
  }

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

// ─── Shortcuts ───────────────────────────────
useShortcut("r", () => {
  toggleEmailBox();
});
useShortcut("c", () => {
  toggleCommentBox();
});
useShortcut("e", () => {
  openFloatingComposer();
});

// Overlays that open outside the composer but belong to it.
const IGNORED_SELECTORS = [
  ".tippy-content",
  ".PopoverContent",
  '[role="dialog"]',
  '[role="presentation"]',
  '[role="menu"]',
  ".dialog-overlay",
  "[data-reka-popper-content-wrapper]",
  // Grammarly suggestions appear outside the box, allow them to stop collapsing.
  "grammarly-extension",
  "grammarly-popups",
  "[data-grammarly-part]",
];

function isIgnored(event: Event): boolean {
  const target = event.target as HTMLElement | null;
  return Boolean(target?.closest?.(IGNORED_SELECTORS.join(", ")));
}

onClickOutside(
  rootRef,
  (event) => {
    // A floating window lives outside the page flow — only the docked
    // composer closes on outside clicks.
    if (windowMode.value !== "docked") return;
    if (justResized.value) return;
    if (isIgnored(event)) return;
    closeComposer();
  },
  {
    ignore: IGNORED_SELECTORS,
  }
);

onMounted(() => {
  // Published for the command palette, which opens the email box itself
  // before inserting. See modalStates.ts.
  replyComposer.value = applySavedReplies;
  agentStore.loadOnce();
});

onBeforeUnmount(() => {
  replyComposer.value = null;
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
/* The composer body caps itself at 50vh; release it when the window height is
   fixed so the body fills and the toolbar pins to the bottom. */
.ticket-composer-window[data-state="floating"] .max-h-\[50vh\],
.ticket-composer-window.composer-resized[data-state="docked"] .max-h-\[50vh\] {
  max-height: none;
}
</style>
