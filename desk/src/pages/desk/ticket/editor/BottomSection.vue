<template>
  <span>
    <TextEditorBottom
      v-model:attachments="editor.attachments"
      :editor="editor.tiptap"
      @content-cleared="clean"
    >
      <template #actions-left>
        <div class="flex h-7 w-7 items-center justify-center">
          <Icon
            icon="lucide:message-square"
            class="h-4 w-4 cursor-pointer text-gray-700"
            @click="showCannedResponses = true"
          />
        </div>
        <div class="flex h-7 w-7 items-center justify-center">
          <Icon
            icon="lucide:book-open"
            class="h-4 w-4 cursor-pointer text-gray-700"
            @click="showArticleResponse = true"
          />
        </div>
      </template>
      <template #actions-right>
        <div class="space-x-2">
          <Button
            label="Comment"
            :disabled="isDisabled"
            theme="gray"
            variant="subtle"
            @click="newComment"
          >
            <template #prefix>
              <Icon icon="lucide:message-square" class="h-4 w-4" />
            </template>
          </Button>
          <Button
            label="Reply"
            :disabled="isDisabled"
            theme="gray"
            variant="solid"
            @click="newCommunication"
          >
            <template #prefix>
              <Icon icon="lucide:send" class="h-4 w-4" />
            </template>
          </Button>
        </div>
      </template>
    </TextEditorBottom>
    <ArticleResponses
      :show="showArticleResponse"
      @close="showArticleResponse = false"
      @contentVal="(val) => (editor.content = val)"
    />
    <CannedResponses
      :show="showCannedResponses"
      @close="showCannedResponses = false"
    />
  </span>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";
import { createResource, Button } from "frappe-ui";
import { Icon } from "@iconify/vue";
import { useAuthStore } from "@/stores/auth";
import TextEditorBottom from "@/components/text-editor/TextEditorBottom.vue";
import { createToast } from "@/utils/toasts";
import { useTicketStore } from "../data";
import CannedResponses from "./CannedResponses.vue";
import ArticleResponses from "./ArticleResponses.vue";

const authStore = useAuthStore();
const { clean, editor, ticket } = useTicketStore();
const showArticleResponse = ref(false);
const showCannedResponses = ref(false);

const insertRes = createResource({
  url: "frappe.client.insert",
  debounce: 500,
  onSuccess() {
    clean();
  },
  validate() {
    if (editor.tiptap?.isEmpty) {
      return "Message is empty";
    }
  },
  onError(error) {
    createToast({
      title: error.message,
      text: error.messages?.join("\n"),
      icon: "x",
      iconClasses: "text-red-500",
    });
  },
});

const isDisabled = computed(
  () =>
    editor.tiptap?.isEmpty || ticket.replyViaAgent.loading || insertRes.loading
);

function newCommunication() {
  ticket.replyViaAgent.loading = true;
  ticket.replyViaAgent.submit({
    attachments: editor.attachments.map((x) => x.name),
    cc: editor.cc.join(","),
    bcc: editor.bcc.join(","),
    message: editor.content,
  });
}

function newComment() {
  insertRes.loading = true;
  insertRes.submit({
    doc: {
      doctype: "HD Ticket Comment",
      reference_ticket: ticket.doc.name,
      content: editor.content,
      commented_by: authStore.userId,
    },
  });
}
</script>
