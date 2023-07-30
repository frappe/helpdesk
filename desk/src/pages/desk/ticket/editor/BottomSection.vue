<template>
  <span>
    <TextEditorBottom
      v-model:attachments="editor.attachments"
      :editor="editor.tiptap"
      @content-cleared="editor.clean()"
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
            @click="addComment.submit()"
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
            @click="addResponse.submit()"
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
import { emitter } from "@/emitter";
import { createToast } from "@/utils/toasts";
import TextEditorBottom from "@/components/text-editor/TextEditorBottom.vue";
import CannedResponses from "./CannedResponses.vue";
import ArticleResponses from "./ArticleResponses.vue";
import { useTicketStore, useTicket } from "../data";

const { editor } = useTicketStore();
const ticket = useTicket();
const data = computed(() => ticket.value.data);
const showArticleResponse = ref(false);
const showCannedResponses = ref(false);

const isDisabled = computed(
  () => editor.tiptap?.isEmpty || addComment.loading || addResponse.loading
);

const addComment = createResource({
  url: "run_doc_method",
  debounce: 300,
  makeParams: () => ({
    dt: "HD Ticket",
    dn: data.value.name,
    method: "new_comment",
    args: {
      content: editor.content,
    },
  }),
  onSuccess: () => {
    emitter.emit("update:ticket");
    editor.clean();
  },
  onError: () => {
    createToast({
      title: "Error adding comment",
      icon: "x",
      iconClasses: "text-red-600",
    });
  },
});

const addResponse = createResource({
  url: "run_doc_method",
  debounce: 300,
  makeParams: () => ({
    dt: "HD Ticket",
    dn: data.value.name,
    method: "reply_via_agent",
    args: {
      attachments: editor.attachments.map((x) => x.name),
      cc: editor.cc.join(","),
      bcc: editor.bcc.join(","),
      message: editor.content,
    },
  }),
  onSuccess: () => {
    emitter.emit("update:ticket");
    editor.clean();
  },
  onError: () => {
    createToast({
      title: "Error replying to ticket",
      icon: "x",
      iconClasses: "text-red-600",
    });
  },
});
</script>
