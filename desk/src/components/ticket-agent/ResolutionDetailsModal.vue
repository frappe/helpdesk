<template>
  <Dialog v-model:open="show" :title="__('Resolution details')">
    <template #default>
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
            :placeholder="__('Describe what fixed the issue')"
          >
            <template #default>
              <EditorContent
                :class="[
                  'prose-sm max-w-none min-h-[7rem] max-h-[40vh] overflow-y-auto px-3 py-2',
                  getFontFamily(resolutionDetails),
                ]"
              />
              <div
                class="flex items-center overflow-x-auto border-t px-2 py-1.5"
              >
                <EditorFixedMenu :items="ticketToolbar" />
              </div>
            </template>
          </Editor>
        </div>
        <div class="flex justify-end gap-2">
          <Button :label="__('Cancel')" @click="show = false" />
          <Button
            variant="solid"
            :loading="isSaving"
            :label="__('Mark as {0}', [status])"
            @click="saveResolution"
          />
        </div>
      </div>
    </template>
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
const isSaving = ref(false);
const editorRef = ref<any>(null);

// Minus mentions: this note is written for the customer.
const extensions = buildEditorExtensions();

watch(show, async (open) => {
  if (!open) return;
  resolutionDetails.value = ticket.value?.doc?.resolution_details || "";
  await nextTick();
  editorRef.value?.editor?.commands.focus();
});

// Asked of the editor: untouched markup is still `<p></p>`, and a lone screenshot is not empty.
function saveResolution() {
  if (isSaving.value) return;
  isSaving.value = true;
  ticket.value.setValue.submit(
    {
      status: props.status,
      resolution_details: editorRef.value?.editor?.isEmpty
        ? ""
        : resolutionDetails.value,
    },
    {
      onSuccess() {
        isSaving.value = false;
        show.value = false;
        emit("saved");
      },
      onError() {
        isSaving.value = false;
      },
    }
  );
}
</script>
