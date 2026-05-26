<template>
  <Dialog
    v-model="open"
    :options="{
      title: __('Bulk Reply {0} ticket(s)', String(selections.size)),
      size: '2xl',
    }"
  >
    <template #body-content>
      <div class="flex flex-col gap-4">
        <SavedReplyEditor
          ref="editorRef"
          :show-signature="true"
          :type="'Email'"
          :placeholder="__('Write your reply...')"
          :min-height="'h-[130px]'"
          @keydown="handleKeydown"
        />
      </div>
    </template>
    <template #actions>
      <div class="flex items-center justify-end gap-2">
        <Button :label="__('Cancel')" @click="open = false" />
        <Button
          variant="solid"
          :label="
            selections.size === 1
              ? __('Send 1 Reply')
              : __('Send {0} Replies', String(selections.size))
          "
          :loading="bulkReplyResource.loading"
          @click="handleSubmit"
        />
      </div>
    </template>
  </Dialog>
</template>

<script setup lang="ts">
import SavedReplyEditor from "@/components/SavedReplyEditor.vue";
import { __ } from "@/translation";
import { Resource } from "@/types";
import { createResource, Dialog, toast } from "frappe-ui";
import { ref, watch } from "vue";

const open = defineModel<boolean>();

const props = defineProps<{
  selections: Set<string>;
}>();

const editorRef = ref<InstanceType<typeof SavedReplyEditor> | null>(null);

watch(open, (val) => {
  if (val) editorRef.value?.reset();
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
      message: editorRef.value?.getContent() ?? "",
    },
    {
      onSuccess() {
        const msg =
          props.selections.size === 1
            ? __("Reply queued — it will be sent to 1 ticket shortly.")
            : __(
                "Replies queued — they will be sent to {0} tickets shortly.",
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
