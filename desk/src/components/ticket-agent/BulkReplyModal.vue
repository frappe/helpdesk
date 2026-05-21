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
        <p class="text-p-sm text-ink-gray-6">
          {{ __("Sending a reply to {0} ticket(s).", [selections.size]) }}
        </p>
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
            __('Send {0} Repl{1}', [
              selections.size,
              selections.size === 1 ? 'y' : 'ies',
            ])
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
import { createResource, Dialog } from "frappe-ui";
import { ref, watch } from "vue";

const open = defineModel<boolean>();

const props = defineProps<{
  selections: Set<string>;
}>();

const editorRef = ref<InstanceType<typeof SavedReplyEditor> | null>(null);

watch(open, (val) => {
  if (val) editorRef.value?.reset();
});

const bulkReplyResource = createResource({
  url: "helpdesk.api.ticket.bulk_reply",
  onSuccess() {
    open.value = false;
  },
});

function handleSubmit() {
  if (editorRef.value?.isEmpty()) return;
  bulkReplyResource.submit({
    ticket_ids: Array.from(props.selections),
    message: editorRef.value?.getContent() ?? "",
  });
}

function handleKeydown(e: KeyboardEvent) {
  if ((e.metaKey || e.ctrlKey) && e.key === "Enter") {
    e.preventDefault();
    handleSubmit();
  }
}
</script>
