<template>
  <span v-if="ticket.data">
    <TopBar
      :title="ticket.data.subject"
      :back-to="{ name: CUSTOMER_PORTAL_LANDING }"
    >
      <template #bottom>
        <div class="flex items-center gap-1 text-base text-gray-600">
          <span># {{ ticket.data.name }}</span>
          <Icon icon="lucide:dot" class="h-4 w-4" />
          <Badge
            :label="transformStatus(ticket.data.status)"
            :theme="colorMapCustomer[ticket.data.status]"
            variant="subtle"
          />
        </div>
      </template>
      <template #right>
        <Button
          v-if="showReopenButton"
          label="Reopen"
          theme="gray"
          variant="outline"
          @click="setValue.submit({ fieldname: 'status', value: 'Open' })"
        >
          <template #prefix>
            <Icon icon="lucide:repeat-2" class="h-4 w-4" />
          </template>
        </Button>
        <Button
          v-if="showResolveButton"
          label="Mark as resolved"
          theme="gray"
          variant="outline"
          @click="showFeedbackDialog = !showFeedbackDialog"
        >
          <template #prefix>
            <Icon icon="lucide:check" class="h-4 w-4" />
          </template>
        </Button>
      </template>
    </TopBar>
    <div class="flex flex-col gap-6 px-9 py-4 text-base text-gray-900">
      <div v-for="c in ticket.data.communications" :key="c.name">
        <CommunicationItem
          :content="c.content"
          :date="c.creation"
          :sender="c.sender"
          :sender-image="c.sender"
          :cc="c.cc"
          :bcc="c.bcc"
          :attachments="c.attachments"
        />
      </div>
      <TextEditor
        v-if="stateActive.includes(ticket.data.status)"
        ref="textEditor"
        :placeholder="placeholder"
        :content="editorContent"
        @change="(v) => (editorContent = v)"
      >
        <template #bottom="{ editor }">
          <TextEditorBottom v-model:attachments="attachments" :editor="editor">
            <template #actions-right>
              <Button
                label="Send"
                :disabled="editor.isEmpty"
                theme="gray"
                variant="solid"
                @click="newCommunication.submit()"
              />
            </template>
          </TextEditorBottom>
        </template>
      </TextEditor>
    </div>
    <Dialog
      v-model="showFeedbackDialog"
      :options="{
        title: 'Rate this ticket',
        actions: [
          {
            label: 'Submit',
            theme: 'gray',
            variant: 'solid',
            onClick: () =>
              setValue.submit({
                fieldname: {
                  status: 'Resolved',
                  feedback: feedbackPreset,
                  feedback_extra: feedbackText,
                },
              }),
          },
        ],
      }"
    >
      <template #body-content>
        <div class="space-y-4 text-base text-gray-700">
          <div class="space-y-2">
            <span> Select a rating </span>
            <StarRating v-model:rating="feedbackRating" :static="false" />
          </div>
          <div v-if="feedbackOptions.data?.length" class="space-y-2">
            <span> Pick an option </span>
            <div class="flex flex-wrap gap-2">
              <Button
                v-for="o in feedbackOptions.data"
                :key="o.name"
                :label="o.label"
                :theme="feedbackPreset === o.name ? 'green' : 'gray'"
                variant="subtle"
                @click="feedbackPreset = o.name"
              />
            </div>
          </div>
          <FormControl
            v-model="feedbackText"
            type="textarea"
            placeholder="Tell us more"
          />
        </div>
      </template>
    </Dialog>
  </span>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from "vue";
import {
  createResource,
  createListResource,
  Badge,
  Button,
  Dialog,
  FormControl,
} from "frappe-ui";
import { Icon } from "@iconify/vue";
import { CUSTOMER_PORTAL_LANDING } from "@/router";
import { socket } from "@/socket";
import { createToast } from "@/utils/toasts";
import { useTicketStatusStore } from "@/stores/ticketStatus";
import CommunicationItem from "@/components/CommunicationItem.vue";
import StarRating from "@/components/StarRating.vue";
import TextEditor from "@/components/text-editor/TextEditor.vue";
import TextEditorBottom from "@/components/text-editor/TextEditorBottom.vue";
import TopBar from "@/components/TopBar.vue";

const props = defineProps({
  ticketId: {
    type: String,
    required: true,
  },
});

const { colorMapCustomer, stateActive } = useTicketStatusStore();
const textEditor = ref(null);
const placeholder = "Type a message";
const editorContent = ref("");
const attachments = ref([]);
const showFeedbackDialog = ref(false);
const feedbackRating = ref(0);
const feedbackText = ref("");
const feedbackPreset = ref(null);

const ticket = createResource({
  url: "helpdesk.helpdesk.doctype.hd_ticket.api.get_one",
  params: {
    name: props.ticketId,
  },
  auto: true,
});

const newCommunication = createResource({
  url: "run_doc_method",
  makeParams: () => ({
    dt: "HD Ticket",
    dn: props.ticketId,
    method: "create_communication_via_contact",
    args: {
      message: editorContent.value,
      attachments: Array.from(attachments.value).map((a) => a.name),
    },
  }),
  onSuccess: () => {
    clearEditor();
    ticket.reload();
  },
  debounce: 300,
});

const setValue = createResource({
  url: "frappe.client.set_value",
  debounce: 300,
  makeParams: (params) => {
    return {
      doctype: "HD Ticket",
      name: props.ticketId,
      fieldname: params.fieldname,
      value: params.value,
    };
  },
  onSuccess: () => {
    showFeedbackDialog.value = false;
    ticket.reload();
  },
  onError: (err) => {
    const messages = err.error?.messages;
    const title = messages?.join(", ");

    createToast({
      title,
      icon: "x",
      iconClasses: "text-red-500",
    });
  },
});

const feedbackOptions = createListResource({
  doctype: "HD Ticket Feedback Option",
  fields: ["name", "label"],
  pageLength: 99999,
});

const showReopenButton = computed(
  () => ticket.data.status === "Resolved" && !ticket.data.feedback
);
const showResolveButton = computed(() =>
  ["Open", "Replied"].includes(ticket.data.status)
);

function clearEditor() {
  textEditor.value?.editor.commands.clearContent();
  attachments.value = [];
}

function transformStatus(status: string) {
  switch (status) {
    case "Replied":
      return "Awaiting reply";
    default:
      return status;
  }
}

onMounted(() => {
  socket.on("helpdesk:new-communication", (data) => {
    if (data.ticket_id === parseInt(props.ticketId))
      ticket.getCommunications.reload();
  });
});

onUnmounted(() => {
  socket.off("helpdesk:new-communication");
});

watch(feedbackRating, (rating) => {
  feedbackPreset.value = null;
  feedbackOptions.update({
    filters: {
      rating,
    },
  });
  feedbackOptions.fetch();
});
</script>
