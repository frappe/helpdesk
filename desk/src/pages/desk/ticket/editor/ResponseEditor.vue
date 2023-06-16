<template>
  <div
    class="content mx-auto"
    :style="{
      width: '742px',
    }"
  >
    <div class="my-3.5 flex items-start gap-2.5">
      <Avatar
        :image="authStore.userImage"
        :label="authStore.userName"
        size="xl"
      />
      <TextEditor
        v-if="editor.isExpanded"
        ref="editorRef"
        class="grow"
        :mentions="mentions"
        :placeholder="placeholder"
        :content="editor.content"
        @change="(v) => (editor.content = v)"
      >
        <template #top>
          <TopSection v-if="!configStore.skipEmailWorkflow" />
        </template>
        <template #editor="{ editor: e }">
          <TextEditorContent :editor="e" />
        </template>
        <template #bottom>
          <BottomSection />
        </template>
      </TextEditor>
      <div
        v-else
        class="flex h-8 w-full cursor-pointer select-none items-center rounded-lg border border-gray-300 px-2.5 text-base text-gray-500"
        @click="editor.isExpanded = true"
      >
        {{ placeholder }}
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onUnmounted, ref, watch } from "vue";
import { Avatar, TextEditorContent } from "frappe-ui";
import { useAuthStore } from "@/stores/auth";
import { useAgentStore } from "@/stores/agent";
import { useConfigStore } from "@/stores/config";
import TextEditor from "@/components/text-editor/TextEditor.vue";
import { useTicketStore } from "../data";
import BottomSection from "./BottomSection.vue";
import TopSection from "./TopSection.vue";

const authStore = useAuthStore();
const agentStore = useAgentStore();
const configStore = useConfigStore();
const { editor } = useTicketStore();
const editorRef = ref(null);
const placeholder = "Add a reply / comment";
const mentions = computed(() =>
  agentStore.options.map((a) => ({
    label: a.agent_name,
    value: a.name,
  }))
);

watch(editorRef, (e) => {
  editor.tiptap = e.editor;
  if (editor.tiptap) editor.tiptap?.commands.focus();
});
onUnmounted(() => (editor.isExpanded = false));
</script>
