<template>
  <Dialog :options="options">
    <template #body-content>
      <div class="flex flex-col gap-3 text-xs text-gray-700">
        <div class="grid grid-cols-3 gap-2">
          <div class="flex flex-col gap-1">
            <div class="flex gap-1">
              Ticket Type
              <div class="text-red-500">*</div>
            </div>
            <SearchComplete
              doctype="HD Ticket Type"
              label="Ticket Type"
              @change="ticketType = $event['value']"
            />
          </div>
          <div class="flex w-full flex-col gap-1 place-self-center">
            <div class="flex gap-1">
              Contact
              <div class="text-red-500">*</div>
            </div>
            <SearchComplete
              doctype="Contact"
              label="Ticket Type"
              @change="contact = $event['value']"
            />
          </div>
          <div class="flex w-full flex-col gap-1 place-self-center">
            Customer
            <SearchComplete
              doctype="HD Customer"
              label="Ticket Type"
              @change="customer = $event['value']"
            />
          </div>
        </div>
        <div class="flex flex-col gap-1">
          <div class="flex gap-1">
            Subject
            <div class="text-red-500">*</div>
          </div>
          <Input placeholder="Short message" @input="subject = $event" />
        </div>
        <div class="flex flex-col gap-1">
          <div class="flex gap-1">
            Description
            <div class="text-red-500">*</div>
          </div>
          <TextEditor
            ref="textEditor"
            placeholder="Detailed explanation"
            :content="description"
            @change="description = $event"
          >
            <template #bottom="{ editor }">
              <TextEditorBottom
                :editor="editor"
                :attachments="Array.from(attachments)"
                @attachment-added="(file) => attachments.add(file)"
                @attachment-removed="(file) => attachments.delete(file)"
              >
                <template #actions-right>
                  <Button
                    class="bg-gray-900 text-white hover:bg-gray-800"
                    label="Create"
                    :disabled="isDisabled"
                    @click="insertRes.submit()"
                  />
                </template>
              </TextEditorBottom>
            </template>
          </TextEditor>
        </div>
      </div>
    </template>
  </Dialog>
</template>

<script setup lang="ts">
import { ref, computed } from "vue";
import { createResource, Button } from "frappe-ui";
import { isEmpty } from "lodash";
import { createToast } from "@/utils/toasts";
import SearchComplete from "@/components/SearchComplete.vue";
import TextEditor from "@/components/text-editor/TextEditor.vue";
import TextEditorBottom from "@/components/text-editor/TextEditorBottom.vue";

const emit = defineEmits<{
  (event: "close"): void;
}>();

const subject = ref("");
const description = ref("");
const attachments = ref(new Set([]));
const contact = ref("");
const customer = ref("");
const ticketType = ref("");
const textEditor = ref(null);
const isDisabled = computed(
  () =>
    insertRes.loading ||
    isEmpty(subject.value) ||
    textEditor.value?.editor.isEmpty
);

const insertRes = createResource({
  url: "helpdesk.api.ticket.create_new",
  debounce: 500,
  makeParams() {
    return {
      values: {
        subject: subject.value,
        description: description.value,
        contact: contact.value,
        ticket_type: ticketType.value,
        customer: customer.value,
      },
      attachments: Array.from(attachments.value).map(
        (attachment) => attachment.name
      ),
      via_customer_portal: true,
    };
  },
  validate(params) {
    if (isEmpty(params.values.ticket_type)) return "Ticket type is mandatory";
    if (isEmpty(params.values.subject)) return "Subject should not be empty";
    if (textEditor.value?.editor.isEmpty)
      return "Description should not be empty";
  },
  onError(error) {
    const text = error.message ? error.message : error.messages?.join(", ");

    createToast({
      title: "Error creating ticket",
      text,
      icon: "x",
      iconClasses: "text-red-500",
    });
  },
  onSuccess() {
    createToast({
      title: "Ticket created",
      icon: "check",
      iconClasses: "text-green-500",
    });

    emit("close");
  },
});

const options = {
  title: "New Ticket",
  size: "3xl",
};
</script>
