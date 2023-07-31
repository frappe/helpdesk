<template>
  <span v-if="ticket.data">
    <TopBar
      :title="ticket.data.subject"
      :back-to="{ name: CUSTOMER_PORTAL_LANDING }"
    >
      <template #bottom>
        <div class="flex items-center gap-1 text-base text-gray-600">
          <span># {{ ticket.data.name }}</span>
          <IconDot class="h-4 w-4" />
          <Badge
            :label="transformStatus(ticket.data.status)"
            :theme="colorMapCustomer[ticket.data.status]"
            variant="subtle"
          />
        </div>
      </template>
      <template #right>
        <span v-if="ticket.data.status !== 'Closed'">
          <Button
            v-if="ticket.data.status == 'Resolved'"
            label="Reopen"
            theme="gray"
            variant="outline"
            @click="reopen.submit()"
          >
            <template #prefix>
              <IconRepeat class="h-4 w-4" />
            </template>
          </Button>
          <Button
            v-else
            label="Mark as resolved"
            theme="gray"
            variant="outline"
            @click="resolve.submit()"
          >
            <template #prefix>
              <IconCheck class="h-4 w-4" />
            </template>
          </Button>
        </span>
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
  </span>
</template>

<script setup lang="ts">
import { onMounted, onUnmounted, ref } from "vue";
import { createResource, Badge } from "frappe-ui";
import { CUSTOMER_PORTAL_LANDING } from "@/router";
import { socket } from "@/socket";
import { useTicketStatusStore } from "@/stores/ticketStatus";
import CommunicationItem from "@/components/CommunicationItem.vue";
import TextEditor from "@/components/text-editor/TextEditor.vue";
import TextEditorBottom from "@/components/text-editor/TextEditorBottom.vue";
import TopBar from "@/components/TopBar.vue";
import IconCheck from "~icons/lucide/check";
import IconDot from "~icons/lucide/dot";
import IconRepeat from "~icons/lucide/repeat-2";

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

const reopen = createResource({
  url: "run_doc_method",
  makeParams: () => ({
    dt: "HD Ticket",
    dn: props.ticketId,
    method: "reopen",
  }),
  onSuccess: () => ticket.reload(),
  debounce: 300,
});

const resolve = createResource({
  url: "run_doc_method",
  makeParams: () => ({
    dt: "HD Ticket",
    dn: props.ticketId,
    method: "resolve",
  }),
  onSuccess: () => ticket.reload(),
  debounce: 300,
});

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
</script>
