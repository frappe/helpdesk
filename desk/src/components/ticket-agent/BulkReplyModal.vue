<template>
  <Dialog
    v-model="open"
    :options="{
      title: __('Bulk Reply'),
      size: '2xl',
    }"
  >
    <template #body-content>
      <div class="flex flex-col gap-4">
        <p class="text-p-sm">
          <CompactEditor
            ref="editorRef"
            v-model="content"
            :show-signature="true"
            :show-attachments="true"
            :type="'Email'"
            :placeholder="__('Write your reply...')"
            :min-height="'min-h-[130px]'"
            :max-height="'max-h-[250px]'"
            @keydown="handleKeydown"
          />
        </p>
      </div>
    </template>
    <template #actions>
      <div class="flex items-center justify-end gap-2">
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
import { createResource, Dialog, toast } from "frappe-ui";
import { ref, watch } from "vue";

const open = defineModel<boolean>();

const props = defineProps<{
  selections: Set<string>;
}>();

const content = ref("");
const editorRef = ref<InstanceType<typeof CompactEditor> | null>(null);

watch(open, (val) => {
  if (val) {
    content.value = "";
    editorRef.value?.reset();
  }
});

const bulkReplyResource: Resource = createResource({
  url: "helpdesk.api.ticket.bulk_reply",
  onSuccess() {
    open.value = false;
  },
});

function handleSubmit() {
  if (editorRef.value?.isEmpty()) return;
  bulkReplyResource.submit(
    {
      ticket_ids: Array.from(props.selections),
      message: content.value,
      attachments: (editorRef.value?.attachments ?? []).map((a: any) => a.name),
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
