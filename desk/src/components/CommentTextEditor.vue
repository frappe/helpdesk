<template>
  <TextEditor
    v-if="agentsList.data"
    ref="editorRef"
    :editor-class="[
      'prose-sm max-w-none',
      editable &&
        'min-h-[7rem] mx-6 md:ml-10 md:mr-9 max-h-[50vh] overflow-y-auto border-t py-3',
      getFontFamily(newComment),
    ]"
    :content="newComment"
    :starterkit-options="{ heading: { levels: [2, 3, 4, 5, 6] } }"
    :placeholder="placeholder"
    :editable="editable"
    :mentions="agents"
    @change="editable ? (newComment = $event) : null"
    :extensions="[PreserveVideoControls]"
    :uploadFunction="(file:any)=>uploadFunction(file, doctype, ticketId)"
  >
    <template #bottom>
      <div v-if="editable" class="flex flex-col gap-2 px-6 md:pl-10 md:pr-9">
        <!-- Attachments -->
        <div class="flex flex-wrap gap-2">
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
        <!-- Fixed Menu -->
        <div class="flex justify-between overflow-hidden border-t py-2.5">
          <div class="flex items-center overflow-x-auto w-[60%]">
            <TextEditorFixedMenu
              class="-ml-1"
              :buttons="textEditorMenuButtons"
            />
            <FileUploader
              :upload-args="{
                doctype: doctype,
                docname: ticketId,
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
          <div class="flex items-center justify-end space-x-2 w-[40%]">
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
import { computed, onBeforeUnmount, onMounted, ref, watch } from "vue";

import { AttachmentItem } from "@/components/";
import { AttachmentIcon } from "@/components/icons/";
import { useTyping } from "@/composables/realtime";
import { useAgentStore } from "@/stores/agent";
import { useAuthStore } from "@/stores/auth";
import { PreserveVideoControls } from "@/tiptap-extensions";
import {
  getFontFamily,
  isContentEmpty,
  removeAttachmentFromServer,
  textEditorMenuButtons,
  uploadFunction,
} from "@/utils";
import { useStorage } from "@vueuse/core";

const { updateOnboardingStep } = useOnboarding("helpdesk");
const { agents: agentsList } = useAgentStore();
const { isManager } = useAuthStore();

onMounted(() => {
  if (
    agentsList.loading ||
    agentsList.data?.length ||
    agentsList.list.promise
  ) {
    return;
  }
  agentsList.fetch();
});

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

// Initialize typing composable
const { onUserType, cleanup } = useTyping(props.ticketId);

const attachments = ref([]);
const commentEmpty = computed(() => {
  return isContentEmpty(newComment.value);
});
const loading = ref(false);

// Watch for changes in comment content to trigger typing events
watch(newComment, (newValue, oldValue) => {
  if (newValue !== oldValue && newValue) {
    onUserType();
  }
});

onBeforeUnmount(() => {
  cleanup();
});

const label = computed(() => {
  return loading.value ? "Sending..." : props.label;
});

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

defineExpose({
  submitComment,
  editor,
});
</script>
