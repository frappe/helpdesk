<template>
  <Dialog v-model:open="open" :title="__('Reply')" size="2xl">
    <template #default>
      <div class="flex flex-col gap-4">
        <p class="text-p-sm">
          <CompactEditor
            ref="editorRef"
            v-model="content"
            v-model:attachments="attachments"
            :show-signature="true"
            :show-attachments="true"
            :placeholder="__('Write your reply...')"
            :min-height="'min-h-[200px]'"
            :max-height="'max-h-[300px]'"
            :upload-fn="handleFileUpload"
            @keydown="handleKeydown"
          />
        </p>
        <div
          v-if="failures.length"
          role="alert"
          class="text-p-sm text-ink-gray-9"
        >
          <p>{{ __("Replies failed for these tickets:") }}</p>
          <ul class="list-disc pl-5">
            <li v-for="failure in failures" :key="failure.ticket_id">
              {{ failure.ticket_id }}: {{ failure.error }}
            </li>
          </ul>
        </div>
      </div>
    </template>
    <template #actions>
      <div class="flex items-center justify-end gap-2">
        <Button :label="__('Discard')" @click="handleDiscard" />
        <Button
          variant="solid"
          :loading="bulkReplyResource.loading"
          :disabled="editorRef?.isUploading || bulkReplyResource.loading"
          @click="handleSubmit"
          :label="
            pendingTicketIds.length === 1
              ? __('Send Reply')
              : __('Send to {0} tickets', String(pendingTicketIds.length))
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
import { computed, ref, watch } from "vue";

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

type BulkReplyResult = {
  sent: string[];
  failed: { ticket_id: string; error: string }[];
};
const failures = ref<BulkReplyResult["failed"]>([]);
let responseGeneration = 0;
const pendingTicketIds = computed(() =>
  failures.value.length
    ? failures.value.map((failure) => failure.ticket_id)
    : Array.from(props.selections)
);
watch(
  () => Array.from(props.selections).join(","),
  () => {
    responseGeneration++;
    failures.value = [];
  },
  { flush: "sync" }
);
// Retry state belongs to one modal session. The component stays mounted, so
// reopening with the same selection must target the whole selection again.
watch(
  open,
  (isOpen) => {
    responseGeneration++;
    if (isOpen) failures.value = [];
  },
  { flush: "sync" }
);

const bulkReplyResource: Resource = createResource({
  url: "helpdesk.api.ticket.bulk_reply",
});

function clearDraft() {
  content.value = "";
  editorRef.value?.reset();
  failures.value = [];
}

function attachmentKey() {
  return (attachments.value ?? []).map((a) => a.name).join("\n");
}

async function handleFileUpload(file: File, options?: any) {
  const uploads = await Promise.all(
    pendingTicketIds.value.map((ticketId) =>
      uploadFunction(file, "HD Ticket", ticketId, true, options)
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
  if (editorRef.value?.isEmpty() || bulkReplyResource.loading) return;
  const requestGeneration = responseGeneration;
  const submittedMessage = content.value;
  const submittedAttachments = attachmentKey();
  bulkReplyResource.submit(
    {
      ticket_ids: pendingTicketIds.value,
      message: submittedMessage,
      attachments: (attachments.value ?? []).map((a) => a.name),
    },
    {
      onSuccess(result: BulkReplyResult) {
        // A response must not change the draft or retry targets of a newer session.
        if (!open.value || requestGeneration !== responseGeneration) {
          // Fully sent: drop the draft so reopening cannot resend it, unless
          // the agent has already edited it (text or attachments) for a newer reply.
          if (
            !result.failed.length &&
            content.value === submittedMessage &&
            attachmentKey() === submittedAttachments
          ) {
            content.value = "";
            editorRef.value?.reset();
          }
          toast.info(
            __(
              "A previous bulk reply finished: sent to {0} tickets, failed for {1} tickets.",
              String(result.sent.length),
              String(result.failed.length)
            )
          );
          return;
        }
        failures.value = result.failed;
        if (result.failed.length) {
          const msg = result.sent.length
            ? __(
                "Sent replies to {0} of {1} tickets. Retry will only include failed tickets.",
                String(result.sent.length),
                String(result.sent.length + result.failed.length)
              )
            : __("No replies were sent. Check the errors and try again.");
          if (result.sent.length) toast.warning(msg);
          else toast.error(msg);
          return;
        }
        const msg =
          result.sent.length === 1
            ? __("Bulk reply sent successfully to 1 ticket.")
            : __(
                "Bulk reply sent successfully to {0} tickets.",
                String(result.sent.length)
              );
        toast.success(msg);
        clearDraft();
        open.value = false;
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
<template>
  <Dialog v-model:open="open" :title="__('Reply')" size="2xl">
    <template #default>
      <div class="flex flex-col gap-4">
        <p class="text-p-sm">
          <CompactEditor
            ref="editorRef"
            v-model="content"
            v-model:attachments="attachments"
            :show-signature="true"
            :show-attachments="true"
            :placeholder="__('Write your reply...')"
            :min-height="'min-h-[200px]'"
            :max-height="'max-h-[300px]'"
            :upload-fn="handleFileUpload"
            @keydown="handleKeydown"
          />
        </p>
        <div
          v-if="failures.length"
          role="alert"
          class="text-p-sm text-ink-gray-9"
        >
          <p>{{ __("Replies failed for these tickets:") }}</p>
          <ul class="list-disc pl-5">
            <li v-for="failure in failures" :key="failure.ticket_id">
              {{ failure.ticket_id }}: {{ failure.error }}
            </li>
          </ul>
        </div>
      </div>
    </template>
    <template #actions>
      <div class="flex items-center justify-end gap-2">
        <Button :label="__('Discard')" @click="handleDiscard" />
        <Button
          variant="solid"
          :loading="bulkReplyResource.loading"
          :disabled="editorRef?.isUploading || bulkReplyResource.loading"
          @click="handleSubmit"
          :label="
            pendingTicketIds.length === 1
              ? __('Send Reply')
              : __('Send to {0} tickets', String(pendingTicketIds.length))
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
import { computed, ref, watch } from "vue";

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

type BulkReplyResult = {
  sent: string[];
  failed: { ticket_id: string; error: string }[];
};
const failures = ref<BulkReplyResult["failed"]>([]);
let responseGeneration = 0;
const pendingTicketIds = computed(() =>
  failures.value.length
    ? failures.value.map((failure) => failure.ticket_id)
    : Array.from(props.selections)
);
watch(
  () => Array.from(props.selections).join(","),
  () => {
    responseGeneration++;
    failures.value = [];
  },
  { flush: "sync" }
);
// Retry state belongs to one modal session. The component stays mounted, so
// reopening with the same selection must target the whole selection again.
watch(
  open,
  (isOpen) => {
    responseGeneration++;
    if (isOpen) failures.value = [];
  },
  { flush: "sync" }
);

const bulkReplyResource: Resource = createResource({
  url: "helpdesk.api.ticket.bulk_reply",
});

function clearDraft() {
  content.value = "";
  editorRef.value?.reset();
  failures.value = [];
}

async function handleFileUpload(file: File, options?: any) {
  const uploads = await Promise.all(
    pendingTicketIds.value.map((ticketId) =>
      uploadFunction(file, "HD Ticket", ticketId, true, options)
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
  if (editorRef.value?.isEmpty() || bulkReplyResource.loading) return;
  const requestGeneration = responseGeneration;
  const submittedMessage = content.value;
  bulkReplyResource.submit(
    {
      ticket_ids: pendingTicketIds.value,
      message: submittedMessage,
      attachments: (attachments.value ?? []).map((a) => a.name),
    },
    {
      onSuccess(result: BulkReplyResult) {
        // A response must not change the draft or retry targets of a newer session.
        if (!open.value || requestGeneration !== responseGeneration) {
          // Fully sent: drop the draft so reopening cannot resend it, unless
          // the agent has already edited it for a newer reply.
          if (!result.failed.length && content.value === submittedMessage) {
            content.value = "";
            editorRef.value?.reset();
          }
          toast.info(
            __(
              "A previous bulk reply finished: sent to {0} tickets, failed for {1} tickets.",
              String(result.sent.length),
              String(result.failed.length)
            )
          );
          return;
        }
        failures.value = result.failed;
        if (result.failed.length) {
          const msg = result.sent.length
            ? __(
                "Sent replies to {0} of {1} tickets. Retry will only include failed tickets.",
                String(result.sent.length),
                String(result.sent.length + result.failed.length)
              )
            : __("No replies were sent. Check the errors and try again.");
          if (result.sent.length) toast.warning(msg);
          else toast.error(msg);
          return;
        }
        const msg =
          result.sent.length === 1
            ? __("Bulk reply sent successfully to 1 ticket.")
            : __(
                "Bulk reply sent successfully to {0} tickets.",
                String(result.sent.length)
              );
        toast.success(msg);
        clearDraft();
        open.value = false;
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
