<template>
  <Dialog v-model:open="show" :title="__('Resolution details')">
    <div class="flex flex-1 flex-col gap-4">
      <div class="flex flex-col gap-1.5">
        <span class="text-base-medium text-ink-gray-8">{{
          __("What did you do?")
        }}</span>
        <span class="text-p-sm text-ink-gray-6">{{
          __(
            "The customer sees this on their ticket. Leave it empty to continue without a note."
          )
        }}</span>
      </div>
      <div
        class="rounded border border-outline-gray-2"
        @keydown.ctrl.enter.capture.stop="saveResolution"
        @keydown.meta.enter.capture.stop="saveResolution"
      >
        <Editor
          ref="editorRef"
          v-model="resolutionDetails"
          :extensions="extensions"
          :placeholder="
            __('Re-synced the auth server; codes are accepted again.')
          "
        >
          <template #default>
            <EditorContent
              :class="[
                'prose-sm max-w-none min-h-[7rem] max-h-[40vh] overflow-y-auto px-3 py-2',
                getFontFamily(resolutionDetails),
              ]"
            />
            <div class="flex items-center overflow-x-auto border-t px-2 py-1.5">
              <EditorFixedMenu :items="ticketToolbar" />
            </div>
          </template>
        </Editor>
      </div>
      <div class="flex justify-end gap-2">
        <Button :label="__('Cancel')" @click="show = false" />
        <Button
          variant="solid"
          :loading="ticket.setValue.loading"
          :label="__('Mark as {0}', [status])"
          @click="saveResolution"
        />
      </div>
    </div>
  </Dialog>
</template>

<script setup lang="ts">
import {
  buildEditorExtensions,
  ticketToolbar,
} from "@/components/editor/config";
import { __ } from "@/translation";
import { TicketSymbol } from "@/types";
import { getFontFamily } from "@/utils";
import { Button, Dialog } from "frappe-ui";
import { Editor, EditorContent, EditorFixedMenu } from "frappe-ui/editor";
import { inject, nextTick, ref, watch } from "vue";

const props = withDefaults(defineProps<{ status?: string }>(), {
  status: "Closed",
});
const ticket = inject(TicketSymbol)!;
const show = defineModel<boolean>({ default: false });
const emit = defineEmits<{ saved: [] }>();

const resolutionDetails = ref("");
const editorRef = ref<any>(null);

// no mentions: the customer reads this note
const extensions = buildEditorExtensions();

watch(show, async (open) => {
  if (!open) return;
  resolutionDetails.value = ticket.value?.doc?.resolution_details || "";
  await nextTick();
  editorRef.value?.editor?.commands.focus();
});

// the editor's isEmpty, not the markup: `<p></p>` reads as content, a lone image does not
function saveResolution() {
  if (ticket.value.setValue.loading) return;
  ticket.value.setValue.submit(
    {
      status: props.status,
      resolution_details: editorRef.value?.editor?.isEmpty
        ? ""
        : resolutionDetails.value,
    },
    {
      onSuccess() {
        show.value = false;
        emit("saved");
      },
    }
  );
}
</script>
