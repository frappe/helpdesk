<template>
  <TextEditor
    v-if="agentsList.data"
    ref="textEditor"
    :editor-class="[
      'prose-sm max-w-none',
      editable &&
        'min-h-[7rem] mx-10 max-h-[50vh] overflow-y-auto border-t py-3',
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
        <div
          class="flex justify-between gap-2 overflow-hidden border-t px-10 py-2.5"
        >
          <div class="flex items-center overflow-x-auto">
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
          <div class="mt-2 flex items-center justify-end space-x-2 sm:mt-0">
            <Button
              label="Discard"
              @click="
                () => {
                  newComment = '';
                  emit('discard');
                }
              "
            />
            <Button
              variant="solid"
              label="Submit"
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
import { computed, ref, onMounted } from "vue";
import {
  TextEditorFixedMenu,
  TextEditor,
  FileUploader,
  createResource,
} from "frappe-ui";

import { AttachmentIcon } from "@/components/icons/";
import { AttachmentItem } from "@/components/";
import { useAgentStore } from "@/stores/agent";
import { useStorage } from "@vueuse/core";
import { PreserveVideoControls } from "@/tiptap-extensions";
import { isContentEmpty, textEditorMenuButtons } from "@/utils";

const { agents: agentsList } = useAgentStore();
onMounted(() => {
  agentsList.fetch();
});
const props = defineProps({
  placeholder: {
    type: String,
    default: null,
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
const attachments = useStorage("commentBoxAttachments" + doc.value.name, []);
const newComment = useStorage("commentBoxContent" + doc.value.name, "");
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
    return;
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
      emit("submit");
      loading.value = false;
      attachments.value = null;
      newComment.value = null;
    },
    onError: () => {
      loading.value = false;
    },
  });

  comment.submit();
}
defineExpose({
  submitComment,
});
</script>
