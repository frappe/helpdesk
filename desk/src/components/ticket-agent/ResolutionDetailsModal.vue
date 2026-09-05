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
          @keydown.ctrl.enter.capture.stop="submit"
          @keydown.meta.enter.capture.stop="submit"
        >
          <Editor
            ref="editorRef"
            v-model="details"
            :extensions="extensions"
            :placeholder="
              __('Re-synced the auth server; codes are accepted again.')
            "
          >
            <template #default>
              <EditorContent
                :class="[
                  'prose-sm max-w-none min-h-[7rem] max-h-[40vh] overflow-y-auto px-3 py-2',
                  getFontFamily(details),
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
            @click="submit"
          />
        </div>
      </div>
    </template>
  </Dialog>
</template>

<script setup lang="ts">
// Asked when an agent moves a ticket into the Resolved category, so the account of the fix
// is written while it is still in their head. It lands in `resolution_details`, which is
// what the customer portal shows on its resolution card — the customer otherwise sees only
// the last reply.
//
// Keyed on the category rather than on "Closed" alone, so it also catches Resolved and any
// custom status a helpdesk files under it. The chosen status arrives as a prop because the
// dialog is what finally writes it.
//
// Never blocks the transition: the note is optional, and submitting empty behaves exactly
// as picking the status from the dropdown used to.
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
const emit = defineEmits(["saved"]);

const details = ref("");
const isSaving = ref(false);
const editorRef = ref<any>(null);

// The same editor the reply composer uses, minus mentions: this note is written for the
// customer, and there is nobody to mention in it.
const extensions = buildEditorExtensions();

watch(show, async (open) => {
  if (!open) return;
  // Whatever is already recorded, so reopening the dialog edits rather than discards it.
  details.value = ticket.value?.doc?.resolution_details || "";
  await nextTick();
  editorRef.value?.editor?.commands.focus();
});

// One write, so the note and the status can never disagree. An untouched editor still
// reports `<p></p>`, which would give the customer's resolution card an empty body instead
// of its "no details" line — so nothing written means nothing saved. Asked of the editor
// rather than of the markup, because a note that is only a screenshot is not empty.
function submit() {
  if (isSaving.value) return;
  isSaving.value = true;
  ticket.value.setValue.submit(
    {
      status: props.status,
      resolution_details: editorRef.value?.editor?.isEmpty ? "" : details.value,
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
