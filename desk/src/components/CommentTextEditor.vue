<template>
  <Editor
    ref="editorRef"
    v-model="newComment"
    :extensions="extensions"
    :editable="editable"
    :placeholder="placeholder"
    :upload-function="(file:any)=>uploadFunction(file, doctype, ticketId)"
  >
    <template #default="{ isEmpty }">
      <EditorContent
        :class="[
          'prose-sm max-w-none',
          editable &&
            'min-h-[7rem] mx-5 max-h-[44vh] overflow-y-auto border-t py-3',
          getFontFamily(newComment),
        ]"
      />
      <!-- Attachments -->
      <div class="flex flex-wrap gap-2 my-2 ms-5">
        <AttachmentItem
          v-for="a in attachments"
          :key="a.file_url"
          :label="a.file_name"
          :url="!['MOV', 'MP4'].includes(a.file_type) ? a.file_url : null"
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
      <div v-if="editable" class="flex flex-col gap-2 border-t">
        <div class="px-4">
          <!-- Fixed Menu -->
          <div class="flex justify-between overflow-hidden py-2.5">
            <div class="flex items-center overflow-x-auto w-[60%]">
              <div class="inline-flex items-center gap-1.5 p-1">
                <FileUploader
                  :upload-args="{
                    doctype: doctype,
                    docname: ticketId,
                    private: true,
                  }"
                  @success="(f) => attachments.push(f)"
                >
                  <template #default="{ openFileSelector, uploading }">
                    {{ void (loading = uploading) }}
                    <button
                      class="flex rounded p-1 text-ink-gray-8 transition-colors focus-within:ring-0 hover:bg-surface-gray-3"
                      @click="openFileSelector()"
                      :disabled="uploading"
                    >
                      <AttachmentIcon
                        class="h-4 w-4"
                        style="stroke-width: 1.5 !important"
                      />
                    </button>
                  </template>
                </FileUploader>
                <div class="h-4 w-[2px] border-s ml-1" />
              </div>
              <EditorFixedMenu :items="fullToolbar" />
            </div>
            <div class="flex items-center justify-end gap-x-2 w-[40%]">
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
                :disabled="isDisabled"
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
      </div>
    </template>
  </Editor>
</template>
<script setup lang="ts">
import { FileUploader, createResource } from "frappe-ui";
import { Editor, EditorContent, EditorFixedMenu } from "frappe-ui/editor";
import { useOnboarding } from "frappe-ui/frappe";
import { computed, onBeforeUnmount, onMounted, ref, watch } from "vue";

import { AttachmentItem } from "@/components/";
import { buildEditorExtensions, fullToolbar } from "@/components/editor/config";
import { AttachmentIcon } from "@/components/icons/";
import { useTyping } from "@/composables/realtime";
import { useAgentStore } from "@/stores/agent";
import { useAuthStore } from "@/stores/auth";
import {
  getFontFamily,
  isContentEmpty,
  removeAttachmentFromServer,
  uploadFunction,
} from "@/utils";
import { useStorage } from "@vueuse/core";
import { storeToRefs } from "pinia";

const { updateOnboardingStep } = useOnboarding("helpdesk");
const { agents: agentsList, dropdown } = storeToRefs(useAgentStore());
const { isManager } = useAuthStore();

const props = defineProps({
  ticketId: {
    type: String,
    default: null,
  },
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

const newComment = useStorage("commentBoxContent" + props.ticketId, null);

// Mentions as a reactive getter so the `@` list stays in sync as agents load.
const extensions = buildEditorExtensions({
  mentions: () =>
    (dropdown.value ?? []).map((a: { label: string; value: string }) => ({
      id: a.value,
      label: a.label,
    })),
});

// Initialize typing composable
const { onUserType, cleanup } = useTyping(props.ticketId);

const attachments = ref([]);
const isDisabled = computed(() => {
  return isContentEmpty(newComment.value) || loading.value;
});
const loading = ref(false);

function removeAttachment(attachment) {
  attachments.value = attachments.value.filter((a) => a !== attachment);
  removeAttachmentFromServer(attachment.name);
}

async function submitComment() {
  if (isContentEmpty(newComment.value)) {
    return false;
  }
  const comment = createResource({
    url: "run_doc_method",
    makeParams: () => ({
      dt: props.doctype,
      dn: props.ticketId,
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

// Watch for changes in comment content to trigger typing events
watch(newComment, (newValue, oldValue) => {
  if (newValue !== oldValue && newValue) {
    onUserType();
  }
});

onMounted(() => {
  if (
    agentsList.value.loading ||
    agentsList.value.data?.length ||
    agentsList.value.list.promise
  ) {
    return;
  }
  agentsList.value.fetch();
});

onBeforeUnmount(() => {
  cleanup();
  if (isContentEmpty(newComment.value)) {
    localStorage.removeItem("commentBoxContent" + props.ticketId);
  }
});

defineExpose({
  submitComment,
  editor,
});
</script>
