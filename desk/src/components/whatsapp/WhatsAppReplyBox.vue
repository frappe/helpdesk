<template>
  <div class="border-t" data-testid="whatsapp-composer">
    <p
      v-if="whatsapp.conversation && !whatsapp.conversation.to"
      class="flex items-center gap-2 px-6 py-4 text-p-base text-ink-gray-7 md:px-5"
      data-testid="whatsapp-no-recipient"
    >
      <span
        class="lucide-info size-4 shrink-0 text-ink-gray-5"
        aria-hidden="true"
      />
      {{ __("This contact has not messaged on WhatsApp yet") }}
    </p>
    <div
      v-else-if="whatsapp.conversation && !whatsapp.windowOpen"
      class="flex flex-col gap-3 px-6 py-4 sm:flex-row sm:items-center sm:justify-between md:px-5"
      data-testid="whatsapp-template-only"
    >
      <p class="flex items-center gap-2 text-p-base text-ink-gray-7">
        <span
          class="lucide-info size-4 shrink-0 text-ink-amber-5"
          aria-hidden="true"
        />
        {{
          __(
            "The 24-hour reply window has closed. Send an approved template to restart the conversation."
          )
        }}
      </p>
      <Button
        class="shrink-0"
        variant="solid"
        :label="__('Send Template')"
        @click="showTemplates = true"
      />
    </div>
    <div v-else class="flex flex-col gap-2 px-6 py-3 md:px-5">
      <SavedReplyActions
        ref="savedReplyActions"
        :ticket-id="whatsapp.ticketName"
        doctype="HD Ticket"
      />
      <MessageInput
        ref="input"
        v-bind="whatsapp.messages"
        :sender-name="whatsapp.contactName || __('Contact')"
        :placeholder="__('Type a WhatsApp message')"
        :you-label="__('You')"
        :upload-document-label="__('Upload Document')"
        :upload-image-label="__('Upload Image')"
        :upload-video-label="__('Upload Video')"
        :caption-placeholder="__('Add a caption...')"
        :send-label="__('Send')"
        :replying-to-label="__('Replying to')"
        :dismiss-reply-label="__('Dismiss reply')"
        window-closed-label=""
        window-unopened-label=""
        @send="onSent"
      >
        <template #leading-actions>
          <Button
            variant="ghost"
            :tooltip="__('Saved replies')"
            :aria-label="__('Saved replies')"
            icon="lucide-zap"
            @click="showSavedReplies = true"
          />
          <Button
            variant="ghost"
            :tooltip="__('Templates')"
            :aria-label="__('Templates')"
            icon="lucide-layout-template"
            @click="showTemplates = true"
          />
        </template>
      </MessageInput>
    </div>
    <WhatsAppTemplatePicker
      v-if="whatsapp.enabled"
      v-model="showTemplates"
      :ticket="ticket?.doc ?? {}"
      :to="whatsapp.conversation?.to"
      :allowed="whatsapp.conversation?.templates ?? []"
      @sent="onTemplateSent"
    />
    <SavedRepliesSelectorModal
      v-model="showSavedReplies"
      doctype="HD Ticket"
      :ticket-id="whatsapp.ticketName"
      @apply="applySavedReply"
    />
  </div>
</template>

<script setup lang="ts">
import SavedRepliesSelectorModal from "@/components/SavedRepliesSelectorModal.vue";
import SavedReplyActions from "@/components/SavedReplyActions/SavedReplyActions.vue";
import { replyComposer } from "@/pages/ticket/modalStates";
import { __ } from "@/translation";
import { TicketSymbol, type RenderedSavedReply } from "@/types";
import { getErrorMessage } from "@helpdesk/shared/utils";
import { MessageInput } from "@whatsapp/ui";
import { Button, call } from "frappe-ui";
import { inject, onBeforeUnmount, onMounted, ref, useTemplateRef } from "vue";
import type { TicketWhatsApp } from "./useTicketWhatsApp";
import WhatsAppTemplatePicker from "./WhatsAppTemplatePicker.vue";

const props = defineProps<{ whatsapp: TicketWhatsApp }>();
const emit = defineEmits<{ sent: [] }>();
const ticket = inject(TicketSymbol, null);

const input = useTemplateRef<{ focus: () => void }>("input");
const savedReplyActions =
  useTemplateRef<InstanceType<typeof SavedReplyActions>>("savedReplyActions");
const showTemplates = ref(false);
const showSavedReplies = ref(false);

function onSent() {
  savedReplyActions.value?.submit();
  emit("sent");
}

// the two controllers are independent, so a template send refreshes the thread itself
function onTemplateSent() {
  props.whatsapp.messages.reload();
  emit("sent");
}

/** Insert a saved reply as WhatsApp text and stage its actions for the send. */
async function applySavedReply(reply: RenderedSavedReply) {
  const text = reply.name && (await renderSavedReply(reply.name));
  if (!text) return;
  const draft = props.whatsapp.messages.draft;
  props.whatsapp.messages.setDraft(draft ? `${draft}\n${text}` : text);
  savedReplyActions.value?.add(reply);
  focus();
}

function renderSavedReply(savedReply: string): Promise<string | null> {
  return call("helpdesk.integrations.whatsapp.api.render_saved_reply", {
    ticket: props.whatsapp.ticketName,
    saved_reply: savedReply,
  }).catch((error: unknown) => {
    getErrorMessage(error, true, __("Could not insert the saved reply"));
    return null;
  });
}

function focus() {
  input.value?.focus();
}

// published for the command palette, as EmailEditor does
onMounted(() => (replyComposer.value = applySavedReply));

onBeforeUnmount(() => {
  if (replyComposer.value === applySavedReply) replyComposer.value = null;
});

defineExpose({ focus });
</script>
