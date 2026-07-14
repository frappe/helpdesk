<template>
  <div class="flex flex-col gap-2 border-t px-6 md:px-5 py-3">
    <!-- Reply preview -->
    <div
      v-if="reply?.name"
      class="flex items-start justify-between gap-2 rounded-md border-s-2 border-ink-green-3 bg-surface-gray-2 px-2 py-1 text-p-xs text-ink-gray-6"
    >
      <div class="min-w-0">
        <div class="font-medium text-ink-gray-7">
          {{ reply.from_name || __("You") }}
        </div>
        <div class="line-clamp-2">{{ replyPreview }}</div>
      </div>
      <FeatherIcon
        name="x"
        class="size-4 cursor-pointer"
        @click="reply = null"
      />
    </div>

    <!-- Pending attachment -->
    <div v-if="attach" class="flex items-center gap-2">
      <AttachmentItem :label="attachName" :url="attach">
        <template #suffix>
          <FeatherIcon
            name="x"
            class="size-3.5 cursor-pointer"
            @click="clearAttachment"
          />
        </template>
      </AttachmentItem>
    </div>

    <div class="flex items-end gap-2">
      <div class="flex items-center gap-1">
        <!-- Attach -->
        <FileUploader
          :upload-args="{
            doctype: 'HD Ticket',
            docname: ticketId,
            private: true,
          }"
          @success="onUpload"
        >
          <template #default="{ openFileSelector, uploading }">
            <Dropdown :options="uploadOptions(openFileSelector)">
              <Button variant="ghost" :loading="uploading">
                <template #icon><AttachmentIcon class="size-4" /></template>
              </Button>
            </Dropdown>
          </template>
        </FileUploader>

        <!-- Emoji -->
        <IconPicker @update:model-value="onEmoji">
          <template #default="{ togglePopover }">
            <Button variant="ghost" @click="togglePopover()">
              <template #icon
                ><FeatherIcon name="smile" class="size-4"
              /></template>
            </Button>
          </template>
        </IconPicker>

        <!-- Templates -->
        <Button variant="ghost" @click="showTemplates = true">
          <template #icon
            ><FeatherIcon name="file-text" class="size-4"
          /></template>
        </Button>
      </div>

      <textarea
        ref="textareaRef"
        v-model="content"
        rows="1"
        :placeholder="__('Type a message')"
        class="form-textarea flex-1 resize-none rounded-lg border-none bg-surface-gray-2 text-p-sm focus:ring-0"
        @keydown.enter="onEnter"
      />

      <Button
        variant="solid"
        theme="green"
        :loading="sendMessageResource.loading"
        :disabled="isEmpty"
        @click="send()"
      >
        <template #icon><FeatherIcon name="send" class="size-4" /></template>
      </Button>
    </div>

    <WhatsAppTemplateSelectorModal
      v-model="showTemplates"
      @send="sendTemplate"
    />
  </div>
</template>

<script setup lang="ts">
import { AttachmentItem } from "@/components";
import { AttachmentIcon } from "@/components/icons";
import IconPicker from "@/components/IconPicker.vue";
import WhatsAppTemplateSelectorModal from "@/components/whatsapp/WhatsAppTemplateSelectorModal.vue";
import { __ } from "@/translation";
import { TicketContactSymbol, WhatsAppActivity } from "@/types";
import {
  Button,
  Dropdown,
  FeatherIcon,
  FileUploader,
  createResource,
  toast,
} from "frappe-ui";
import { computed, inject, nextTick, ref } from "vue";

const props = defineProps({
  ticketId: { type: String, required: true },
});

const emit = defineEmits<{ submit: [] }>();

// The whole conversation is anchored on the ticket's Contact; sends carry the
// ticket id too so the message records which ticket it came from.
const contact = inject(TicketContactSymbol);

const content = ref("");
const attach = ref("");
const contentType = ref<"text" | "image" | "video" | "document">("text");
const reply = ref<WhatsAppActivity | null>(null);
const showTemplates = ref(false);
const textareaRef = ref<HTMLTextAreaElement | null>(null);

const contactName = computed(() => contact?.value?.data?.name);
const toNumber = computed(
  () => contact?.value?.data?.mobile_no || contact?.value?.data?.phone
);
const isEmpty = computed(() => !content.value.trim() && !attach.value);
const attachName = computed(() => attach.value.split("/").pop() || "");
const replyPreview = computed(() => reply.value?.message || "");

// Guard the destination up front: without a number, warn and do nothing —
// notably before opening the file picker, so a media file is never uploaded
// only to be undeliverable.
function ensureNumber(): boolean {
  if (contactName.value && toNumber.value) return true;
  toast.warning(__("This contact has no WhatsApp number."));
  return false;
}

function uploadOptions(openFileSelector: (mime?: string) => void) {
  const pick = (type: string, mime?: string) => {
    if (!ensureNumber()) return;
    contentType.value = type;
    openFileSelector(mime);
  };
  return [
    { label: __("Photo"), onClick: () => pick("image", "image/*") },
    { label: __("Video"), onClick: () => pick("video", "video/*") },
    { label: __("Document"), onClick: () => pick("document") },
  ];
}

// The destination number is derived from the contact server-side; the client
// never sends it. `toNumber` here only drives the "no number" hint below.
const sendMessageResource = createResource({
  url: "helpdesk.integrations.whatsapp.api.create_whatsapp_message",
  makeParams: () => ({
    contact: contactName.value,
    message: content.value,
    attach: attach.value,
    reply_to: reply.value?.name || "",
    content_type: contentType.value,
    hd_ticket: props.ticketId,
  }),
  onSuccess: () => {
    resetState();
    emit("submit");
  },
  onError: (e: Error) => toast.error(e.message || __("Could not send message")),
  debounce: 300,
});

const sendTemplateResource = createResource({
  url: "helpdesk.integrations.whatsapp.api.send_whatsapp_template",
  onSuccess: () => emit("submit"),
  onError: (e: Error) =>
    toast.error(e.message || __("Could not send template")),
});

function send() {
  if (isEmpty.value) return;
  if (!ensureNumber()) return;
  sendMessageResource.submit();
}

function sendTemplate(template: string) {
  showTemplates.value = false;
  if (!ensureNumber()) return;
  sendTemplateResource.submit({
    contact: contactName.value,
    template,
    hd_ticket: props.ticketId,
  });
}

function onUpload(file: { file_url: string }) {
  attach.value = file.file_url;
  // A media upload is itself the message — fire it straight away, mirroring the
  // "attach and send" behaviour of a real WhatsApp client. The number was
  // already checked before the picker opened.
  send();
}

function onEmoji(emoji: string) {
  if (!emoji) return;
  content.value += emoji;
  nextTick(() => textareaRef.value?.focus());
}

function onEnter(e: KeyboardEvent) {
  // Don't send while an IME candidate is being composed (CJK, dead keys).
  if (e.isComposing || e.keyCode === 229) return;
  if (e.shiftKey) return; // Shift+Enter inserts a newline
  e.preventDefault();
  send();
}

function clearAttachment() {
  attach.value = "";
  contentType.value = "text";
}

function resetState() {
  content.value = "";
  clearAttachment();
  reply.value = null;
}

function setReply(activity: WhatsAppActivity) {
  reply.value = activity;
  nextTick(() => textareaRef.value?.focus());
}

defineExpose({ setReply });
</script>
