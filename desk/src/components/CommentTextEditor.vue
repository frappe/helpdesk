<template>
  <TextEditor
    v-if="agentsList.data"
    ref="editorRef"
    :editor-class="[
      'prose-sm max-w-none',
      editable &&
        'min-h-[7rem] mx-10 max-h-[50vh] overflow-y-auto border-t py-3',
      getFontFamily(newComment),
    ]"
    :content="newComment"
    :starterkit-options="{ heading: { levels: [2, 3, 4, 5, 6] } }"
    :placeholder="placeholder"
    :editable="editable"
    :mentions="agents"
    @change="editable ? (newComment = $event) : null"
    :extensions="[PreserveVideoControls]"
  >
    <template #bottom>
      <div v-if="editable" class="flex flex-col gap-2">
        <!-- Attachments -->
        <div class="flex flex-wrap gap-2 px-10">
          <AttachmentItem
            v-for="a in attachments"
            :key="a.file_url"
            :label="a.file_name"
          >
            <template #suffix>
              <FeatherIcon
                class="h-3.5"
                name="x"
                @click.stop="removeAttachment(a)"
              />
            </template>
          </AttachmentItem>
        </div>
        <!-- Fixed Menu -->
        <div
          class="flex justify-between gap-2 overflow-hidden border-t px-10 py-2.5"
        >
          <div class="flex items-center overflow-x-auto w-4/6">
            <TextEditorFixedMenu
              class="-ml-1"
              :buttons="textEditorMenuButtons"
            />
            <FileUploader
              :upload-args="{
                doctype: doctype,
                docname: modelValue.name,
                private: true,
              }"
              @success="(f) => attachments.push(f)"
            >
              <template #default="{ openFileSelector }">
                <Button
                  theme="gray"
                  variant="ghost"
                  @click="openFileSelector()"
                >
                  <template #icon>
                    <AttachmentIcon
                      class="h-4"
                      style="color: #000000; stroke-width: 1.5 !important"
                    />
                  </template>
                </Button>
              </template>
            </FileUploader>
          </div>
          <div
            class="mt-2 flex items-center justify-end space-x-2 sm:mt-0 w-2/6"
          >
            <Button
              label="Discard"
              @click="
                () => {
                  newComment = '';
                  attachments = [];
                  emit('discard');
                }
              "
            />
            <Button
              variant="solid"
              :label="label"
              :disabled="commentEmpty"
              :loading="loading"
              @click="
                () => {
                  loading = true;
                  submitComment();
                  newComment = '';
                }
              "
            />
          </div>
        </div>
      </div>
    </template>
  </TextEditor>
</template>
<script setup lang="ts">
import {
  FileUploader,
  TextEditor,
  TextEditorFixedMenu,
  createResource,
} from "frappe-ui";
import { useOnboarding } from "frappe-ui/frappe";
import { computed, onMounted, ref } from "vue";

import { AttachmentItem } from "@/components/";
import { AttachmentIcon } from "@/components/icons/";
import { useAgentStore } from "@/stores/agent";

import { useAuthStore } from "@/stores/auth";
import { PreserveVideoControls } from "@/tiptap-extensions";
import { getFontFamily, isContentEmpty, textEditorMenuButtons } from "@/utils";
import { useStorage } from "@vueuse/core";

const { updateOnboardingStep } = useOnboarding("helpdesk");
const { agents: agentsList } = useAgentStore();
const { isManager } = useAuthStore();

onMounted(() => {
  //TODO: check this out
  if (!agentsList.fetched) {
    agentsList.fetch();
  }
});
const props = defineProps({
  placeholder: {
    type: String,
    default: null,
  },
  label: {
    type: String,
    default: "Comment",
  },
  editable: {
    type: Boolean,
    default: true,
  },
  doctype: {
    type: String,
    default: "HD Ticket",
  },
});

const emit = defineEmits(["submit", "discard"]);
const doc = defineModel();
const newComment = useStorage("commentBoxContent" + doc.value.name, "");
const attachments = ref([]);
const commentEmpty = computed(() => {
  return isContentEmpty(newComment.value);
});
const loading = ref(false);

const agents = computed(() => {
  return (
    agentsList.data?.map((agent) => ({
      label: agent.agent_name.trimEnd(),
      value: agent.name,
    })) || []
  );
});

function removeAttachment(attachment) {
  attachments.value = attachments.value.filter((a) => a !== attachment);
}

async function submitComment() {
  if (isContentEmpty(newComment.value)) {
    return false;
  }
  const comment = createResource({
    url: "run_doc_method",
    makeParams: () => ({
      dt: props.doctype,
      dn: doc.value.name,
      method: "new_comment",
      args: {
        content: newComment.value,
        attachments: attachments.value,
      },
    }),
    onSuccess: () => {
      if (isManager) {
        updateOnboardingStep("comment_on_ticket");
      }
      emit("submit");
      loading.value = false;
      attachments.value = [];
      newComment.value = null;
    },
    onError: () => {
      loading.value = false;
    },
  });

  comment.submit();
}

const editorRef = ref(null);
const editor = computed(() => editorRef.value?.editor);

defineExpose({
  submitComment,
  editor,
});
</script>
