<template>
  <div v-if="ticket.data" class="flex flex-col">
    <LayoutHeader>
      <template #left-header>
        <Breadcrumbs :items="breadcrumbs" />
      </template>
      <template #right-header>
        <CustomActions
          v-if="ticket.data._customActions"
          :actions="ticket.data._customActions"
        />
        <Button
          v-if="ticket.data.status !== 'Closed'"
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
    </LayoutHeader>
    <div class="flex overflow-hidden h-full">
      <!-- Main Ticket Comm -->
      <section class="flex flex-col flex-1">
        <!-- show for only mobile -->
        <TicketCustomerTemplateFields v-if="isMobileView" />

        <!-- Section to display relevant tickets -->
        <section v-if="relevantTickets.length" class="p-5">
          <h2 class="text-lg font-bold mb-3">Relevant Tickets</h2>
          <ul>
            <li v-for="relevantTicket in relevantTickets" :key="relevantTicket.name" class="mb-2">
              <div class="p-3 border rounded-lg">
                <h3 class="text-md font-semibold">{{ relevantTicket.subject }}</h3>
                <p>Status: {{ relevantTicket.status }}</p>
                <p>Created on: {{ new Date(relevantTicket.creation).toLocaleDateString() }}</p>
              </div>
            </li>
          </ul>
        </section>
        <TicketConversation class="grow" />
        <div
          class="m-5"
          @keydown.ctrl.enter.capture.stop="sendEmail"
          @keydown.meta.enter.capture.stop="sendEmail"
        >
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
                :disabled="$refs.editor?.editor.isEmpty || send.loading"
                :loading="send.loading"
                @click="sendEmail"
              />
            </template>
          </TicketTextEditor>
        </div>
      </section>
      <!-- Ticket Sidebar only for desktop view-->
      <TicketCustomerSidebar v-if="!isMobileView" @open="isExpanded = true" />
    </div>
    <TicketFeedback v-model:open="showFeedbackDialog" />
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, provide, ref } from "vue";
import { createResource, Button, Breadcrumbs, call } from "frappe-ui";
import { useConfigStore } from "@/stores/config";
import { globalStore } from "@/stores/globalStore";
import { Icon } from "@iconify/vue";
import { ITicket } from "./symbols";
import { useRouter } from "vue-router";
import { createToast, isContentEmpty } from "@/utils";
import { setupCustomizations } from "@/composables/formCustomisation";
import { socket } from "@/socket";
import { LayoutHeader } from "@/components";
import { useScreenSize } from "@/composables/screen";
import TicketConversation from "./TicketConversation.vue";
import TicketCustomerTemplateFields from "./TicketCustomerTemplateFields.vue";
import TicketTextEditor from "./TicketTextEditor.vue";
import TicketFeedback from "./TicketFeedback.vue";
import TicketCustomerSidebar from "@/components/ticket/TicketCustomerSidebar.vue";
import { useTicket } from "./data";

const relevantTickets = ref([]);
const loadingRelevantTickets = ref(false);

const fetchRelevantTickets = async () => {
  loadingRelevantTickets.value = true;
  try {
    const response = await call('helpdesk.helpdesk.doctype.hd_ticket.hd_ticket.get_relevant_tickets', {
      contact: ticket.data.contact, 
      company: ticket.data.company,
      subject: ticket.data.subject, 
    });
    relevantTickets.value = response.message || [];
  } catch (error) {
    console.error('Error fetching relevant tickets:', error);
  } finally {
    loadingRelevantTickets.value = false;
  }
};

interface P {
  ticketId: string;
}
const router = useRouter();

const props = defineProps<P>();
const ticket = useTicket(
  props.ticketId,
  true,
  null,
  (data) => {
    setupCustomizations(data, {
      doc: data,
      call,
      router,
      $dialog,
      updateField,
      createToast,
    });
  },
  () => {
    createToast({
      title: "Ticket not found",
      icon: "x",
      iconClasses: "text-red-600",
    });
    router.replace("/my-tickets");
  }
);
provide(ITicket, ticket);
const editor = ref(null);
const placeholder = "Type a message";
const editorContent = ref("");
const attachments = ref([]);
const showFeedbackDialog = ref(false);
const isExpanded = ref(false);

const { isMobileView } = useScreenSize();
const { $dialog } = globalStore();

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

function updateField(name, value, callback = () => {}) {
  updateTicket(name, value);
  callback();
}

function sendEmail() {
  if (isContentEmpty(editorContent.value) || send.loading) {
    return;
  }
  send.submit();
}

function updateTicket(fieldname: string, value: string) {
  createResource({
    url: "frappe.client.set_value",
    params: {
      doctype: "HD Ticket",
      name: props.ticketId,
      fieldname,
      value,
    },
    auto: true,
    onSuccess: () => {
      ticket.reload();
      createToast({
        title: "Ticket updated",
        icon: "check",
        iconClasses: "text-green-600",
      });
    },
  });
}

function handleClose() {
  if (showFeedback.value) {
    showFeedbackDialog.value = true;
  } else {
    showConfirmationDialog();
  }
}

function showConfirmationDialog() {
  $dialog({
    title: "Close Ticket",
    message: "Are you sure you want to close this ticket?",
    actions: [
      {
        label: "Confirm",
        variant: "solid",
        onClick(close: Function) {
          ticket.data.status = "Closed";
          setValue.submit(
            { fieldname: "status", value: "Closed" },
            {
              onSuccess: () => {
                createToast({
                  title: "Ticket closed successfully",
                  icon: "check",
                  iconClasses: "text-green-600",
                  position: "top-right",
                });
              },
            }
          );
          close();
        },
      },
    ],
  });
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
});

const breadcrumbs = computed(() => {
  let items = [{ label: "Tickets", route: { name: "TicketsCustomer" } }];
  items.push({
    label: ticket.data?.subject,
    route: { name: "TicketCustomer" },
  });
  return items;
});

const showEditor = computed(() => ticket.data.status !== "Closed");

// this handles whether the ticket was raised and then was closed without any reply from the agent.
const { isFeedbackMandatory } = useConfigStore();
const showFeedback = computed(() => {
  const hasAgentCommunication = ticket.data?.communications?.some(
    (c) => c.sender !== ticket.data.raised_by
  );
  return hasAgentCommunication && isFeedbackMandatory;
});

onMounted(() => {
  document.title = props.ticketId;
  socket.on("helpdesk:ticket-update", (ticketID) => {
    if (ticketID === Number(props.ticketId)) {
      ticket.reload();
    }
  });

  fetchRelevantTickets();
});

onUnmounted(() => {
  document.title = "Helpdesk";
  socket.off("helpdesk:ticket-update");
});
</script>
