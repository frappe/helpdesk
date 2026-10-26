<template>
  <div class="comm-area" resizable="true">
    <div
      class="flex justify-between gap-3 border-t px-6 md:px-5 py-4 md:py-2.5"
    >
      <div class="flex gap-1.5 items-center">
        <Button
          v-if="!whatsapp || whatsapp.enabled"
          ref="sendEmailRef"
          variant="ghost"
          label="Reply"
          :class="[
            showEmailBox ? '!bg-surface-gray-4 hover:!bg-surface-gray-3' : '',
          ]"
          @click="toggleEmailBox()"
        >
          <template #prefix>
            <component :is="whatsapp ? WhatsAppIcon : EmailIcon" class="h-4" />
          </template>
        </Button>
        <Button
          variant="ghost"
          label="Comment"
          :class="[
            showCommentBox ? '!bg-surface-gray-4 hover:!bg-surface-gray-3' : '',
          ]"
          @click="toggleCommentBox()"
        >
          <template #prefix>
            <CommentIcon class="h-4" />
          </template>
        </Button>
        <TypingIndicator :ticketId="ticketId" />
      </div>
    </div>
    <Transition name="slide">
      <div
        v-show="showEmailBox"
        ref="emailBoxRef"
        @keydown.ctrl.enter.capture.stop="submitEmail"
        @keydown.meta.enter.capture.stop="submitEmail"
        @keydown.esc.capture.stop="showEmailBox = false"
      >
        <div class="overflow-hidden">
          <WhatsAppReplyBox
            v-if="whatsapp"
            ref="whatsAppReplyBoxRef"
            :whatsapp="whatsapp"
            @sent="emit('update')"
          />
          <EmailEditor
            v-else
            ref="emailEditorRef"
            :label="
              isMobileView ? 'Send' : isMac ? 'Send (⌘ + ⏎)' : 'Send (Ctrl + ⏎)'
            "
            placeholder="Hi John, we are looking into this issue."
            :ticketId="ticketId"
            :to-emails="toEmails"
            :cc-emails="ccEmails"
            :bcc-emails="bccEmails"
            @sending="
              () => {
                showEmailBox = false;
              }
            "
            @submit="() => emit('update')"
            @restore="
              () => {
                showEmailBox = true;
              }
            "
            @discard="
              () => {
                showEmailBox = false;
              }
            "
          />
        </div>
      </div>
    </Transition>
    <Transition name="slide">
      <div
        v-show="showCommentBox"
        ref="commentBoxRef"
        @keydown.ctrl.enter.capture.stop="submitComment"
        @keydown.meta.enter.capture.stop="submitComment"
        @keydown.esc.capture.stop="showCommentBox = false"
      >
        <div class="overflow-hidden">
          <CommentTextEditor
            ref="commentTextEditorRef"
            :label="
              isMobileView
                ? 'Comment'
                : isMac
                ? 'Comment (⌘ + ⏎)'
                : 'Comment (Ctrl + ⏎)'
            "
            :ticketId="ticketId"
            :editable="showCommentBox"
            :doctype="doctype"
            placeholder="@John could you please look into this?"
            @sending="
              () => {
                showCommentBox = false;
              }
            "
            @submit="() => emit('update')"
            @restore="
              () => {
                showCommentBox = true;
              }
            "
            @discard="
              () => {
                showCommentBox = false;
              }
            "
          />
        </div>
      </div>
    </Transition>
  </div>
</template>

<script setup lang="ts">
import { CommentTextEditor, EmailEditor, TypingIndicator } from "@/components";
import { CommentIcon, EmailIcon } from "@/components/icons/";
import type { TicketWhatsApp } from "@/components/whatsapp/useTicketWhatsApp";
import WhatsAppIcon from "@/components/whatsapp/WhatsAppIcon.vue";
import WhatsAppReplyBox from "@/components/whatsapp/WhatsAppReplyBox.vue";
import type { WhatsAppMessage } from "@whatsapp/ui";
import { useDevice } from "@/composables";
import { useScreenSize } from "@/composables/screen";
import { useShortcut } from "@helpdesk/shared/shortcuts";
import { showCommentBox, showEmailBox } from "@/pages/ticket/modalStates";
import { onClickOutside } from "@vueuse/core";
import { ref, watch, type PropType } from "vue";

const emit = defineEmits(["update"]);
const content = defineModel("content");
const { isMac } = useDevice();
const { isMobileView } = useScreenSize();
let doc = defineModel();
// let doc = inject(TicketSymbol)?.value.doc
const emailEditorRef = ref(null);
const whatsAppReplyBoxRef = ref<InstanceType<typeof WhatsAppReplyBox> | null>(
  null
);
const commentTextEditorRef = ref(null);
const emailBoxRef = ref(null);
const commentBoxRef = ref(null);

function toggleEmailBox() {
  // a WhatsApp ticket has nothing to reply with without the whatsapp app
  if (props.whatsapp && !props.whatsapp.enabled) return;
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

// the editors emit `submit` once the write lands; reloading here too would
// fetch twice, and the guards' `false` never reaches this side anyway
function submitEmail() {
  // MessageInput sends on Enter itself
  if (props.whatsapp) return;
  emailEditorRef.value.submitMail();
}

function submitComment() {
  commentTextEditorRef.value.submitComment();
}

function splitIfString(str: string | string[]) {
  if (typeof str === "string") {
    return str.split(",");
  }
  return str;
}

function replyToEmail(data: object) {
  if (props.whatsapp) return;
  showEmailBox.value = true;

  emailEditorRef.value.addToReply(
    data.content,
    splitIfString(data.to),
    splitIfString(data.cc),
    splitIfString(data.bcc)
  );
}

function replyToWhatsApp(message: WhatsAppMessage) {
  showEmailBox.value = true;
  props.whatsapp?.messages.setReplyTo(message);
}

const props = defineProps({
  // set on a WhatsApp ticket: the reply box sends through it instead of email
  whatsapp: {
    type: Object as PropType<TicketWhatsApp | null>,
    default: null,
  },
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

watch(
  () => showEmailBox.value,
  (value) => {
    if (!value) return;
    if (props.whatsapp) whatsAppReplyBoxRef.value?.focus();
    else emailEditorRef.value?.editor?.commands?.focus("start");
  }
);

watch(
  () => showCommentBox.value,
  (value) => {
    if (value) {
      commentTextEditorRef.value?.editor?.commands?.focus();
    }
  }
);

useShortcut("r", () => {
  toggleEmailBox();
});
useShortcut("c", () => {
  toggleCommentBox();
});

defineExpose({
  replyToEmail,
  replyToWhatsApp,
  toggleEmailBox,
  toggleCommentBox,
  editor: emailEditorRef,
});

const IGNORED_SELECTORS = [
  ".tippy-box",
  ".tippy-content",
  ".PopoverContent",
  '[role="dialog"]',
  '[role="presentation"]',
  '[role="menu"]',
  ".dialog-overlay",
  // Grammarly suggestions appear outside the box, allow them to stop collapsing.
  "grammarly-extension",
  "grammarly-popups",
  "[data-grammarly-part]",
];

// `ignore` is only consulted on pointerdown, which dialogs stop, so the click
// through has to be checked too. Without this a dialog button closes the box.
function isIgnored(event: Event): boolean {
  const target = event.target as HTMLElement | null;
  return Boolean(target?.closest?.(IGNORED_SELECTORS.join(", ")));
}

onClickOutside(
  emailBoxRef,
  (event) => {
    if (showEmailBox.value && !isIgnored(event)) {
      showEmailBox.value = false;
    }
  },
  {
    ignore: IGNORED_SELECTORS,
  }
);

onClickOutside(
  commentBoxRef,
  (event) => {
    if (showCommentBox.value && !isIgnored(event)) {
      showCommentBox.value = false;
    }
  },
  {
    ignore: IGNORED_SELECTORS,
  }
);
</script>

<style>
@media screen and (max-width: 640px) {
  .comm-area {
    width: 100vw;
  }
}

.slide-enter-active,
.slide-leave-active {
  display: grid;
  transition: grid-template-rows 0.25s ease;
}
.slide-enter-from,
.slide-leave-to {
  grid-template-rows: 0fr;
}
.slide-enter-to,
.slide-leave-from {
  grid-template-rows: 1fr;
}
</style>
