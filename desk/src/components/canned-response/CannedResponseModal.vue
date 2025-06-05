<template>
  <Dialog
    v-model="show"
    :options="{
      size: 'xl',
      actions: [
        {
          label: !isNew ? 'Update' : 'Create',
          variant: 'solid',
          onClick: () => updateItem(),
        },
      ],
    }"
  >
    <template #body-title>
      <div class="flex items-center gap-3">
        <h3 class="text-2xl font-semibold leading-6 text-gray-900">
          {{ !isNew ? "Edit Canned Response" : "Create Canned Response" }}
        </h3>
      </div>
    </template>
    <template #body-content>
      <div class="flex flex-col gap-4">
        <div>
          <div class="mb-1.5 text-sm text-gray-600">{{ "Title" }}</div>
          <TextInput
            v-model="title"
            variant="outline"
            :placeholder="'Customer Query Resolved'"
          />
        </div>
        <div>
          <div class="mb-1.5 text-sm text-gray-600">{{ "Message" }}</div>
          <TextEditor
            ref="content"
            variant="outline"
            editor-class="!prose-sm overflow-auto min-h-[180px] max-h-80 py-1.5 px-2 rounded border border-gray-300 bg-white hover:border-gray-400 hover:shadow-sm focus:bg-white focus:border-gray-500 focus:shadow-sm focus:ring-0 focus-visible:ring-2 focus-visible:ring-gray-400 text-gray-800 transition-colors"
            :bubble-menu="true"
            :content="message"
            :placeholder="'Your query has been resolved. Thank you for reaching out.'"
            @change="(val) => (message = val)"
          />
        </div>
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import { TextEditor, call, TextInput } from "frappe-ui";

const props = defineProps({
  name: {
    type: String,
    required: false,
    default: null,
  },
  isNew: {
    type: Boolean,
    required: false,
    default: false,
  },
});

const show = defineModel();
const title = defineModel("title");
const message = defineModel("message");
const emit = defineEmits(["update"]);

async function updateItem() {
  if (props.name) {
    await call("frappe.client.set_value", {
      doctype: "HD Canned Response",
      name: props.name,
      fieldname: {
        title: title.value,
        message: message.value,
      },
    });
  } else {
    await call("frappe.client.insert", {
      doc: {
        doctype: "HD Canned Response",
        title: title.value,
        message: message.value,
      },
    });
  }
  emit("update");
  show.value = false;
}
</script>
