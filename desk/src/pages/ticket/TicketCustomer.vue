<template>
  <div v-if="ticket.data" class="flex flex-col">
    <TicketBreadcrumbs parent="TicketsCustomer">
      <template #right>
        <Button
          v-if="showReopenButton"
          label="Reopen"
          theme="gray"
          variant="solid"
          @click="setValue.submit({ fieldname: 'status', value: 'Open' })"
        >
          <template #prefix>
            <Icon icon="lucide:repeat-2" />
          </template>
        </Button>
        <Button
          v-if="showResolveButton"
          label="Close"
          theme="gray"
          variant="solid"
          @click="showFeedbackDialog = !showFeedbackDialog"
        >
          <template #prefix>
            <Icon icon="lucide:check" />
          </template>
        </Button>
      </template>
    </TicketBreadcrumbs>
    <TicketCustomerTemplateFields />
    <TicketConversation class="grow" />
    <span class="m-5">
      <TicketTextEditor
        v-if="showEditor"
        ref="editor"
        v-model:attachments="attachments"
        v-model:content="editorContent"
        v-model:expand="isExpanded"
        :placeholder="placeholder"
        autofocus
        @clear="() => (isExpanded = false)"
      >
        <template #bottom-right>
          <Button
            label="Send"
            theme="gray"
            variant="solid"
            :disabled="$refs.editor.editor.isEmpty || send.loading"
            @click="() => send.submit()"
          />
        </template>
      </TicketTextEditor>
    </span>
    <TicketFeedback v-model:open="showFeedbackDialog" />
  </div>
</template>

<script setup lang="ts">
import { computed, provide, ref } from "vue";
import { createResource, Button } from "frappe-ui";
import { Icon } from "@iconify/vue";
import { useError } from "@/composables/error";
import TicketBreadcrumbs from "./TicketBreadcrumbs.vue";
import TicketConversation from "./TicketConversation.vue";
import TicketCustomerTemplateFields from "./TicketCustomerTemplateFields.vue";
import TicketFeedback from "./TicketFeedback.vue";
import TicketTextEditor from "./TicketTextEditor.vue";
import { ITicket } from "./symbols";

interface P {
  ticketId: string;
}

const props = defineProps<P>();
const ticket = createResource({
  url: "helpdesk.helpdesk.doctype.hd_ticket.api.get_one",
  cache: ["Ticket", props.ticketId],
  auto: true,
  params: {
    name: props.ticketId,
  },
});
provide(ITicket, ticket);
const editor = ref(null);
const placeholder = "Type a message";
const editorContent = ref("");
const attachments = ref([]);
const showFeedbackDialog = ref(false);
const isExpanded = ref(false);

const send = createResource({
  url: "run_doc_method",
  debounce: 300,
  makeParams: () => ({
    dt: "HD Ticket",
    dn: props.ticketId,
    method: "create_communication_via_contact",
    args: {
      message: editorContent.value,
      attachments: attachments.value,
    },
  }),
  onSuccess: () => {
    editor.value.editor.commands.clearContent(true);
    attachments.value = [];
    isExpanded.value = false;
    ticket.reload();
  },
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
  onError: useError(),
});

const showReopenButton = computed(
  () => ticket.data.status === "Resolved" && !ticket.data.feedback
);
const showResolveButton = computed(() =>
  ["Open", "Replied"].includes(ticket.data.status)
);

const showEditor = computed(() =>
  ["Open", "Replied", "Resolved"].includes(ticket.data.status)
);
</script>
