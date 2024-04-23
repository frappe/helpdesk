<template>
  <TextEditor
    ref="e"
    :editor-class="[
      'prose-sm max-w-none mx-10 max-h-[50vh] overflow-y-auto border-t py-3',
      true && 'min-h-[7rem]',
    ]"
    :content="content"
    :starterkit-options="{ heading: { levels: [2, 3, 4, 5, 6] } }"
    :placeholder="placeholder"
    :editable="editable"
    @change="editable ? (content = $event) : null"
  >
    <template #top>
      <div
        class="mx-10 flex items-center gap-2 border-t py-2.5"
        :class="[cc || bcc ? 'border-b' : '']"
      >
        <span class="text-xs text-gray-500">TO:</span>
        <MultiSelectInput
          v-model="toEmailsClone"
          class="flex-1"
          :validate="validateEmail"
          :error-message="(value) => `${value} is an invalid email address`"
        />
      </div>
      <div
        v-if="cc"
        class="mx-10 flex items-center gap-2 py-2.5"
        :class="bcc ? 'border-b' : ''"
      >
        <span class="text-xs text-gray-500">CC:</span>
        <MultiSelectInput
          ref="ccInput"
          v-model="ccEmailsClone"
          class="flex-1"
          :validate="validateEmail"
          :error-message="(value) => `${value} is an invalid email address`"
        />
      </div>
      <div v-if="bcc" class="mx-10 flex items-center gap-2 py-2.5">
        <span class="text-xs text-gray-500">BCC:</span>
        <MultiSelectInput
          ref="bccInput"
          v-model="bccEmailsClone"
          class="flex-1"
          :validate="validateEmail"
          :error-message="(value) => `${value} is an invalid email address`"
        />
      </div>
    </template>
    <template #bottom>
      <div
        class="flex justify-between gap-2 overflow-hidden border-t px-10 py-2.5"
      >
        <div class="flex items-center overflow-x-auto">
          <TextEditorFixedMenu class="-ml-1" :buttons="textEditorMenuButtons" />
          <div class="flex gap-1">
            <FileUploader
              :upload-args="{
                doctype: doctype,
                docname: modelValue?.name,
                private: true,
              }"
              @success="(f) => attachments.push(f)"
            >
              <template #default="{ openFileSelector }">
                <Button variant="ghost" @click="openFileSelector()">
                  <template #icon>
                    <AttachmentIcon class="h-4" />
                  </template>
                </Button>
              </template>
            </FileUploader>
            <!-- <Button
              variant="ghost"
              @click="showEmailTemplateSelectorModal = true"
            >
              <template #icon>
                <EmailIcon class="h-4" />
              </template>
            </Button> -->
          </div>
        </div>
        <div class="mt-2 flex items-center justify-end space-x-2 sm:mt-0">
          <Button
            label="Discard"
            @click="
              () => {
                ccEmailsClone = [];
                bccEmailsClone = [];
                cc = false;
                bcc = false;
                emit('discard');
              }
            "
          />
          <Button
            variant="solid"
            :disabled="emailEmpty"
            label="Submit"
            @click="() => {}"
          />
        </div>
      </div>
    </template>
  </TextEditor>
</template>

<script setup lang="ts">
import { defineModel, ref, computed } from "vue";
import { useStorage } from "@vueuse/core";
import {
  FileUploader,
  TextEditor,
  TextEditorFixedMenu,
  createResource,
} from "frappe-ui";
import { validateEmail } from "@/utils";
import { MultiSelectInput } from "@/components";
import { AttachmentIcon } from "@/components/icons";

const props = defineProps({
  placeholder: {
    type: String,
    default: null,
  },
  editable: {
    type: Boolean,
    default: true,
  },
  doctype: {
    type: String,
    default: "HD Ticket",
  },
  submitButtonProps: {
    type: Object,
    default: () => ({}),
  },
  discardButtonProps: {
    type: Object,
    default: () => ({}),
  },
  toEmails: {
    type: Array,
    default: () => [],
  },
  ccEmails: {
    type: Array,
    default: () => [],
  },
  bccEmails: {
    type: Array,
    default: () => [],
  },
});

const newEmail = useStorage("emailBoxContent", "");

const emailEmpty = computed(() => {
  return !newEmail.value || newEmail.value === "<p></p>";
});

const emit = defineEmits(["submit", "discard"]);

const doc = defineModel();
const content = defineModel("content");
const attachments = defineModel("attachments");
const cc = ref(props.ccEmails.length ? true : false);
const bcc = ref(props.bccEmails.length ? true : false);
const toEmailsClone = ref([...props.toEmails]);
const ccEmailsClone = ref([...props.ccEmails]);
const bccEmailsClone = ref([...props.bccEmails]);
const ccInput = ref(null);
const bccInput = ref(null);

function submitMail() {
  const sendMail = createResource({
    url: "run_doc_method",
    makeParams: () => ({
      dt: props.doctype,
      dn: doc.value.data.name,
      method: "reply_via_agent",
      args: {
        attachments: attachments.value.map((x) => x.name),
        cc: ccEmailsClone,
        bcc: bccEmailsClone,
        message: newEmail.value,
      },
    }),
    onSuccess: () => {
      emit("submit");
    },
  });
  sendMail.submit();
}

const textEditorMenuButtons = [
  "Paragraph",
  ["Heading 2", "Heading 3", "Heading 4", "Heading 5", "Heading 6"],
  "Separator",
  "Bold",
  "Italic",
  "Separator",
  "Bullet List",
  "Numbered List",
  "Separator",
  "Align Left",
  "Align Center",
  "Align Right",
  "FontColor",
  "Separator",
  "Image",
  "Video",
  "Link",
  "Blockquote",
  "Code",
  "Horizontal Rule",
  [
    "InsertTable",
    "AddColumnBefore",
    "AddColumnAfter",
    "DeleteColumn",
    "AddRowBefore",
    "AddRowAfter",
    "DeleteRow",
    "MergeCells",
    "SplitCell",
    "ToggleHeaderColumn",
    "ToggleHeaderRow",
    "ToggleHeaderCell",
    "DeleteTable",
  ],
];
</script>
