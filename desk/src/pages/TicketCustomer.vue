<template>
  <div v-if="ticket.data" class="flex flex-col">
    <TicketBreadcrumbs parent="TicketsCustomer" current="TicketCustomer">
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
          @click="handleClose()"
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
import TicketBreadcrumbs from "./ticket/TicketBreadcrumbs.vue";
import TicketConversation from "./ticket/TicketConversation.vue";
import TicketCustomerTemplateFields from "./ticket/TicketCustomerTemplateFields.vue";
import TicketFeedback from "./ticket/TicketFeedback.vue";
import TicketTextEditor from "./ticket/TicketTextEditor.vue";
import { ITicket } from "./ticket/symbols";
import { useRouter } from "vue-router";
import { createToast } from "@/utils";

interface P {
  ticketId: string;
}
const router = useRouter();

const props = defineProps<P>();
const ticket = createResource({
  url: "helpdesk.helpdesk.doctype.hd_ticket.api.get_one",
  cache: ["Ticket", props.ticketId],
  auto: true,
  params: {
    name: props.ticketId,
  },
  onError: () => {
    createToast({
      title: "You are not allowed to view this ticket",
      icon: "x",
      iconClasses: "text-red-600",
    });
    router.replace("/my-tickets");
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

function handleClose() {
  if (showFeedback.value) {
    showFeedbackDialog.value = true;
  } else {
    setValue.submit({ fieldname: "status", value: "Closed" });
  }
}

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

const showFeedback = computed(() => {
  return ticket.data?.communications?.some((c) => {
    if (c.sender !== ticket.data.raised_by) {
      return true;
    }
  });
});
</script>
