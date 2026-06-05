<template>
  <Dialog v-model:open="open" :title="__('Bulk Reply')" size="2xl">
    <template #default>
      <div class="flex flex-col gap-4">
        <p class="text-p-sm">
          <CompactEditor
            ref="editorRef"
            v-model="content"
            v-model:attachments="attachments"
            :show-signature="true"
            :show-attachments="true"
            :type="'Email'"
            :placeholder="__('Write your reply...')"
            :min-height="'min-h-[200px]'"
            :max-height="'max-h-[300px]'"
            :upload-fn="handleFileUpload"
            @keydown="handleKeydown"
          />
        </p>
      </div>
    </template>
    <template #actions>
      <div class="flex items-center justify-end gap-2">
        <Button :label="__('Discard')" @click="handleDiscard" />
        <Button
          variant="solid"
          :loading="bulkReplyResource.loading"
          :disabled="editorRef?.isUploading"
          @click="handleSubmit"
          :label="
            props.selections.size === 1
              ? __('Send Reply')
              : __('Send to {0} tickets', String(props.selections.size))
          "
        />
      </div>
    </template>
  </Dialog>
</template>

<script setup lang="ts">
import CompactEditor from "@/components/CompactEditor.vue";
import { __ } from "@/translation";
import { Resource } from "@/types";
import { uploadFunction } from "@/utils";
import { useStorage } from "@vueuse/core";
import { createResource, Dialog, toast, UploadedFile } from "frappe-ui";
import { ref } from "vue";

const open = defineModel<boolean>();

const props = defineProps<{
  selections: Set<string>;
}>();
const emit = defineEmits<{
  (e: "success"): void;
}>();

const content = useStorage<string>("bulk-reply", "");
const attachments = useStorage<UploadedFile[]>("bulk-attachments", []);
const editorRef = ref<InstanceType<typeof CompactEditor> | null>(null);

const bulkReplyResource: Resource = createResource({
  url: "helpdesk.api.ticket.bulk_reply",
  onSuccess() {
    clearDraft();
    open.value = false;
  },
});

function clearDraft() {
  content.value = "";
  editorRef.value?.reset();
}

async function handleFileUpload(file: File) {
  const uploads = await Promise.all(
    Array.from(props.selections).map((ticketId) =>
      uploadFunction(file, "HD Ticket", ticketId)
    )
  );

  const uploaded = uploads[0];
  if (!uploaded) throw new Error(__("No tickets selected"));
  return uploaded;
}

function handleDiscard() {
  open.value = false;
  clearDraft();
}

function handleSubmit() {
  if (editorRef.value?.isEmpty()) return;
  bulkReplyResource.submit(
    {
      ticket_ids: Array.from(props.selections),
      message: content.value,
      attachments: (attachments.value ?? []).map((a) => a.name),
    },
    {
      onSuccess() {
        const msg =
          props.selections.size === 1
            ? __("Bulk reply sent successfully to 1 ticket.")
            : __(
                "Bulk reply sent successfully to {0} tickets.",
                String(props.selections.size)
              );
        toast.success(msg);
        emit("success");
      },
    }
  );
}

function handleKeydown(e: KeyboardEvent) {
  if ((e.metaKey || e.ctrlKey) && e.key === "Enter") {
    e.preventDefault();
    handleSubmit();
  }
}
</script>
