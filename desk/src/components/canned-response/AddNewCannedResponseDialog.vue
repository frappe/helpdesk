<template>
  <Dialog
    :options="{ title: 'New canned response', size: '3xl' }"
    :show="show"
    class="bg-white px-6 py-5 pb-1 pt-6"
    @close="close()"
  >
    <template #body-content>
      <div class="mt-6 flex flex-col">
        <Input
          id="searchInput"
          v-model="title"
          class="w-full"
          type="text"
          label="Title"
          placeholder="Enter Title"
        />
        <ErrorMessage :message="titleValidationError" />
      </div>
      <div class="mb-2 mt-4 block text-sm leading-4 text-gray-700">Message</div>
      <div>
        <TextEditor
          ref="textEditor"
          class="bg-gray-100"
          editor-class="min-h-[20rem] overflow-y-auto max-h-[73vh] w-full px-3 max-w-full"
          :content="message"
          :starterkit-options="{
            heading: { levels: [2, 3, 4, 5, 6] },
          }"
          @change="
            (val) => {
              message = val;
            }
          "
        >
          <template #top>
            <div>
              <TextEditorFixedMenu
                class="m-3 overflow-x-auto"
                :buttons="textEditorMenuButtons"
              />
            </div>
          </template>
        </TextEditor>
      </div>
      <ErrorMessage :message="messageValidationError" />
    </template>
    <template #actions>
      <Button appearance="primary" class="mr-auto" @click="addResponse()"
        >Add Response</Button
      >
    </template>
  </Dialog>
</template>

<script setup lang="ts">
import { Dialog, Input, ErrorMessage, TextEditor } from "frappe-ui";
import { ref, watch } from "vue";
import { useRouter } from "vue-router";
import { TextEditorFixedMenu } from "frappe-ui/src/components/TextEditor";
import { createResource } from "frappe-ui";

const router = useRouter();

defineProps({
  show: {
    type: Boolean,
    required: true,
  },
});
const emit = defineEmits(["close"]);
const titleValidationError = ref("");
const messageValidationError = ref("");

const title = ref("");
const message = ref("");

watch(title, (value) => {
  validateTitle(value);
});

watch(message, (value) => {
  validateMessage(value);
});

function textEditorMenuButtons() {
  return [
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
    "Separator",
    "Undo",
    "Redo",
  ];
}

function close() {
  title.value = "";
  message.value = "";
  emit("close");
}

function addResponse() {
  if (validateInputs()) {
    return;
  }
  const inputParams = {
    title: title.value,
    message: message.value,
  };
  insert.submit({
    doc: {
      doctype: "HD Canned Response",
      ...inputParams,
    },
  });
}

function validateInputs() {
  let error = validateTitle(title.value);
  error += validateMessage(message.value);

  return error;
}

function validateTitle(value) {
  titleValidationError.value = "";
  if (!value) {
    titleValidationError.value = "Title is required";
  } else if (value.trim() == "") {
    titleValidationError.value = "Title is required";
  }

  return titleValidationError.value;
}

function validateMessage(value) {
  messageValidationError.value = "";
  if (!value) {
    messageValidationError.value = "Message is required";
  } else if (["<p><br></p>", "<p></p>"].includes(value.replaceAll(" ", ""))) {
    messageValidationError.value = "Message is required";
  }

  return messageValidationError.value;
}

const insert = createResource({
  url: "frappe.client.insert",
  onSuccess: (doc) => {
    router.push({
      name: "CannedResponse",
      params: {
        id: doc.name,
      },
    });
  },
  onError: (err) => {
    this.$toast({
      title: "Error while creating canned response",
      text: err,
      icon: "x",
      iconClasses: "text-red-500",
    });
  },
});
</script>
