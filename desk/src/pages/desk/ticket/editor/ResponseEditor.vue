<template>
  <div
    class="content mx-auto"
    :style="{
      width: '742px',
    }"
  >
    <div class="my-3.5 flex items-start gap-2.5">
      <TextEditor
        v-if="editor.isExpanded"
        ref="editorRef"
        v-model="editor.content"
        class="grow"
        :autofocus="true"
        :mentions="mentions"
        :placeholder="placeholder"
        @clear="() => editor.clean()"
      >
        <template #top-right>
          <TabButtons
            v-model="editor.type"
            :buttons="[
              {
                label: 'Comment',
              },
              {
                label: 'Reply',
              },
            ]"
            class="w-max"
          />
        </template>
        <template v-if="editor.type === 'Reply'" #top-bottom>
          <TopSection />
        </template>
        <template #bottom-top>
          <div class="flex flex-wrap gap-2">
            <AttachmentItem
              v-for="a in editor.attachments"
              :key="a.file_url"
              :label="a.file_name"
            >
              <template #suffix>
                <Icon
                  icon="lucide:x"
                  @click.stop="
                    editor.attachments = editor.attachments.filter(
                      (a__) => a__.file_url !== a.file_url
                    )
                  "
                />
              </template>
            </AttachmentItem>
          </div>
        </template>
        <template #bottom-left>
          <Button
            theme="gray"
            variant="ghost"
            @click="showCannedResponses = !showCannedResponses"
          >
            <template #icon>
              <Icon icon="lucide:message-square" />
            </template>
          </Button>
          <Button
            theme="gray"
            variant="ghost"
            @click="showArticleResponse = !showArticleResponse"
          >
            <template #icon>
              <Icon icon="lucide:book-open" />
            </template>
          </Button>
          <FileUploader
            v-if="editor.type === 'Reply'"
            @success="(f: File) => editor.attachments.push(f)"
          >
            <template #default="{ openFileSelector }">
              <Button theme="gray" variant="ghost" @click="openFileSelector()">
                <template #icon>
                  <Icon icon="lucide:paperclip" />
                </template>
              </Button>
            </template>
          </FileUploader>
        </template>
        <template #bottom-right>
          <Button
            :label="editor.type === 'Comment' ? 'Comment' : 'Send'"
            :disabled="isDisabled"
            theme="gray"
            variant="solid"
            @click="
              (editor.type === 'Comment' ? addComment : addResponse).submit()
            "
          >
            <template #prefix>
              <Icon
                :icon="
                  editor.type === 'Comment'
                    ? 'lucide:message-square'
                    : 'lucide:send'
                "
              />
            </template>
          </Button>
        </template>
      </TextEditor>
      <div
        v-else
        class="flex w-full cursor-pointer items-center gap-2 rounded-lg bg-gray-100 px-3.5 py-2 hover:bg-gray-200"
        @click="editor.isExpanded = true"
      >
        <UserAvatar :user="authStore.userId" size="sm" />
        <span class="text-base text-gray-700">{{ placeholder }}</span>
      </div>
    </div>
    <ArticleResponses
      :show="showArticleResponse"
      @close="showArticleResponse = false"
      @contentVal="(val) => (editor.content = val)"
    />
    <CannedResponses
      :show="showCannedResponses"
      @close="showCannedResponses = false"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, onUnmounted, ref, watch } from "vue";
import { createResource, Button, FileUploader, TabButtons } from "frappe-ui";
import { useAgentStore } from "@/stores/agent";
import { useAuthStore } from "@/stores/auth";
import { Icon } from "@iconify/vue";
import { emitter } from "@/emitter";
import { useError } from "@/composables/error";
import { AttachmentItem, TextEditor, UserAvatar } from "@/components";
import CannedResponses from "./CannedResponses.vue";
import ArticleResponses from "./ArticleResponses.vue";
import TopSection from "./TopSection.vue";
import { useTicketStore, useTicket } from "../data";

const ticket = useTicket();
const data = computed(() => ticket.value.data);
const showArticleResponse = ref(false);
const showCannedResponses = ref(false);
const agentStore = useAgentStore();
const authStore = useAuthStore();
const { editor } = useTicketStore();
const editorRef = ref(null);
const placeholder = "Add a reply / comment";
const mentions = computed(() =>
  agentStore.options.map((a) => ({
    label: a.agent_name,
    value: a.name,
  }))
);
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
  onError: useError({ title: "Error adding comment" }),
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
  onError: useError({ title: "Error replying to ticket" }),
});

watch(editorRef, (e) => {
  editor.tiptap = e.editor;
  if (editor.tiptap) editor.tiptap?.commands.focus();
});
onUnmounted(() => (editor.isExpanded = false));
</script>
