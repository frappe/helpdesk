<template>
  <Editor
    ref="editorRef"
    v-model="newComment"
    :extensions="extensions"
    :editable="editable"
    :placeholder="placeholder"
    :upload-function="
      (file: any, options: any) =>
        track(uploadFunction(file, doctype, ticketId, true, options))
    "
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
      <AttachmentList
        class="my-2 ms-5"
        :attachments="attachments"
        @remove="removeAttachment"
      />
      <div v-if="editable" class="flex flex-col gap-2 border-t">
        <div class="px-4">
          <!-- Fixed Menu -->
          <div class="flex justify-between overflow-hidden py-2.5">
            <div class="flex items-center overflow-x-auto w-[60%]">
              <div class="inline-flex items-center gap-1.5 p-1">
                <FileUploader
                  :doctype="doctype"
                  :docname="ticketId"
                  private
                  @success="(f) => attachments.push(f)"
                >
                  <template #default="{ openFileSelector, uploading }">
                    {{ void (loading = uploading) }}
                    <button
                      class="flex rounded-4 p-1 text-ink-gray-8 transition-colors focus-within:ring-0 hover:bg-surface-gray-3"
                      @click="openFileSelector()"
                      :disabled="uploading"
                    >
                      <LoadingIndicator v-if="uploading" class="h-4 w-4" />
                      <AttachmentIcon
                        v-else
                        class="h-4 w-4"
                        style="stroke-width: 1.5 !important"
                      />
                    </button>
                  </template>
                </FileUploader>
                <div class="h-4 w-[2px] border-s ml-1" />
              </div>
              <EditorFixedMenu :items="fullToolbar" />
              <EditorTableMenu />
            </div>
            <div class="flex items-center justify-end gap-x-2 w-[40%]">
              <Button
                label="Discard"
                @click="
                  () => {
                    newComment = '';
                    attachments = [];
                    dropUnused(null);
                    emit('discard');
                  }
                "
              />
              <!-- A disabled button fires no pointer events, so the span
                   carries the hover for the tooltip -->
              <Tooltip
                :text="isUploading ? __('Please wait, media is uploading') : ''"
              >
                <span class="inline-flex">
                  <Button
                    variant="solid"
                    :label="label"
                    :disabled="isDisabled"
                    :loading="loading"
                    @click="submitComment()"
                  />
                </span>
              </Tooltip>
            </div>
          </div>
        </div>
      </div>
    </template>
  </Editor>
</template>
<script setup lang="ts">
import {
  FileUploader,
  LoadingIndicator,
  Tooltip,
  createResource,
  dayjs,
  toast,
} from "frappe-ui";
import {
  Editor,
  EditorContent,
  EditorFixedMenu,
  EditorTableMenu,
} from "frappe-ui/editor";
import { addPendingActivity } from "@framework/ui/ActivityTimeline";
import { useOnboarding } from "@framework/ui";
import { computed, onBeforeUnmount, onMounted, ref, watch } from "vue";

import { AttachmentList } from "@/components/";
import { buildEditorExtensions, fullToolbar } from "@/components/editor/config";
import { AttachmentIcon } from "@/components/icons/";
import { useTyping } from "@/composables/realtime";
import { useUploadTracker } from "@/composables/useUploadTracker";
import { useAgentStore } from "@/stores/agent";
import { useAuthStore } from "@/stores/auth";
import { useUserStore } from "@/stores/user";
import { __ } from "@/translation";
import { capture } from "@/telemetry";
import {
  getFontFamily,
  isContentEmpty,
  removeAttachmentFromServer,
  uploadFunction,
} from "@/utils";
import { useStorage } from "@vueuse/core";
import { storeToRefs } from "pinia";

const { updateOnboardingStep } = useOnboarding("helpdesk") ?? {};
const { agents: agentsList, dropdown } = storeToRefs(useAgentStore());
const authStore = useAuthStore();
const { isManager } = authStore;
const { getUser } = useUserStore();

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

const emit = defineEmits(["submit", "discard", "sending", "restore"]);

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
const { isUploading, track, dropUnused } = useUploadTracker();
const isDisabled = computed(() => {
  return isContentEmpty(newComment.value) || loading.value || isUploading.value;
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
  // The keyboard shortcut reaches here without passing the disabled button
  if (isUploading.value || loading.value) return false;

  const content = newComment.value;
  const sentAttachments = attachments.value;
  const user = getUser(authStore.userId);
  const row = addPendingActivity(props.doctype, props.ticketId, {
    type: "comment",
    timestamp: dayjs().format("YYYY-MM-DD HH:mm:ss"),
    author: {
      email: user?.email,
      fullname: user?.full_name,
      image: user?.user_image,
    },
    data: { name: "", content, attachments: sentAttachments },
  });

  // drop before clearing, or an unmount mid-send deletes what the comment carries
  dropUnused(content);
  newComment.value = null;
  attachments.value = [];
  loading.value = true;
  emit("sending");

  const comment = createResource({
    url: "run_doc_method",
    makeParams: () => ({
      dt: props.doctype,
      dn: props.ticketId,
      method: "new_comment",
      args: { content, attachments: sentAttachments },
    }),
    onSuccess: (res: { message?: string } | string) => {
      // run_doc_method answers with the whole body, since it always carries `docs`
      const name = typeof res === "string" ? res : res?.message;
      // the real row replaces the pending one the moment it arrives; unkeyed,
      // it would outlive it
      name ? row.resolve(`comment:${name}`) : row.drop();
      capture("comment_added");
      if (isManager) {
        updateOnboardingStep?.("comment_on_ticket");
      }
      emit("submit");
      loading.value = false;
    },
    onError: () => {
      toast.error(__("Could not add the comment"));
      row.drop();
      newComment.value = content;
      attachments.value = sentAttachments;
      loading.value = false;
      emit("restore");
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
  // the saved draft still references what it shows, so only what it dropped goes
  dropUnused(newComment.value);
  if (isContentEmpty(newComment.value)) {
    localStorage.removeItem("commentBoxContent" + props.ticketId);
  }
});

defineExpose({
  submitComment,
  editor,
});
</script>
