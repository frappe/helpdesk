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
          :label="__('Close')"
          theme="gray"
          variant="solid"
          @click="handleClose()"
        >
          <template #prefix>
            <LucideCheck class="size-4" />
          </template>
        </Button>
      </template>
    </LayoutHeader>
    <div class="flex overflow-hidden h-full w-full">
      <!-- Main Ticket Comm -->
      <section class="flex flex-col flex-1 w-full md:max-w-[calc(100%-382px)]">
        <div
          v-if="outsideHourSettings.data?.show && !isDismissed"
          class="md:mx-10 md:my-4 justify-between text-lg font-medium mx-6 mb-4 !mt-8"
        >
          <Alert
            v-if="outsideHourSettings.data?.show"
            :title="outsideHourSettings.data?.msg"
            theme="yellow"
            v-model="removeAlert"
          >
          </Alert>
        </div>
        <!-- show for only mobile -->
        <TicketCustomerTemplateFields v-if="isMobileView" />

        <TicketConversation class="grow" />
        <div
          class="w-full p-5"
          @keydown.ctrl.enter.capture.stop="sendEmail"
          @keydown.meta.enter.capture.stop="sendEmail"
        >
          <TicketTextEditor
            v-if="showEditor"
            ref="editor"
            v-model:attachments="attachments"
            v-model:content="editorContent"
            v-model:expand="isExpanded"
            :placeholder="__('Type a message')"
            autofocus
            @clear="() => (isExpanded = false)"
            :uploadFunction="
              (file: any) => uploadFunction(file, 'HD Ticket', props.ticketId)
            "
          >
            <template #bottom-right>
              <Button
                :label="__('Send')"
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
import { LayoutHeader } from "@/components";
import TicketCustomerSidebar from "@/components/ticket/TicketCustomerSidebar.vue";
import { setupCustomizations } from "@/composables/formCustomisation";
import { useActiveViewers } from "@/composables/realtime";
import { useScreenSize } from "@/composables/screen";
import { socket } from "@/socket";
import { useConfigStore } from "@/stores/config";
import { globalStore } from "@/stores/globalStore";
import { useTicketStatusStore } from "@/stores/ticketStatus";
import { isContentEmpty, isCustomerPortal, uploadFunction } from "@/utils";
import {
  Breadcrumbs,
  Button,
  call,
  createResource,
  toast,
  Alert,
} from "frappe-ui";
import { __ } from "@/translation";
import {
  computed,
  defineAsyncComponent,
  onMounted,
  onUnmounted,
  provide,
  ref,
  watch,
} from "vue";
import { useRouter } from "vue-router";
import { ITicket } from "./symbols";
import TicketConversation from "./TicketConversation.vue";
import TicketCustomerTemplateFields from "./TicketCustomerTemplateFields.vue";
import TicketFeedback from "./TicketFeedback.vue";
const TicketTextEditor = defineAsyncComponent(
  () => import("./TicketTextEditor.vue")
);

interface P {
  ticketId: string;
}
const router = useRouter();

const props = defineProps<P>();

const { getStatus } = useTicketStatusStore();

const ticket = createResource({
  url: "helpdesk.helpdesk.doctype.hd_ticket.api.get_one",
  cache: ["Ticket", props.ticketId],
  params: {
    name: props.ticketId,
    is_customer_portal: isCustomerPortal.value,
  },
  auto: true,
  onSuccess: (data) => {
    data.status = getStatus(data.status)?.label_customer;
    setupCustomizations(ticket, {
      doc: data,
      call,
      router,
      toast,
      $dialog,
      updateField,
      createToast: toast.create,
    });
  },
  onError: () => {
    toast.error(__("Ticket not found"));
    router.replace("/my-tickets");
  },
});

provide(ITicket, ticket);
const editor = ref(null);
const editorContent = ref("");
const attachments = ref([]);
const showFeedbackDialog = ref(false);
const isExpanded = ref(false);

const { isMobileView } = useScreenSize();
const { $dialog } = globalStore();
const isDismissed = ref(false);
const removeAlert = ref(true);

watch(removeAlert, (newValue) => {
  if (!newValue) {
    dismissBanner();
  }
});

function getTodayKey() {
  return new Date().toISOString().split("T")[0];
}

function dismissBanner() {
  try {
    const todayKey = getTodayKey();
    localStorage.setItem(`dismissBanner_${props.ticketId}_${todayKey}`, "true");
    isDismissed.value = true;
  } catch (error) {
    console.error("Error saving banner dismissal:", error);
  }
}

onMounted(() => {
  try {
    const todayKey = getTodayKey();
    const dismissed = localStorage.getItem(
      `dismissBanner_${props.ticketId}_${todayKey}`
    );
    isDismissed.value = dismissed === "true";
    cleanupOldBannerDismissals();
  } catch (error) {
    console.error("Error reading banner dismissal:", error);
  }
});

// Clean up old banner dismissal localStorage keys
const cleanupOldBannerDismissals = () => {
  const CLEANUP_KEY = "lastBannerCleanup";
  const ONE_WEEK_MS = 7 * 24 * 60 * 60 * 1000;

  try {
    const lastCleanup = localStorage.getItem(CLEANUP_KEY);
    const now = Date.now();

    if (lastCleanup && now - parseInt(lastCleanup) < ONE_WEEK_MS) {
      return;
    }

    // Find and remove all dismissBanner keys
    const keysToRemove: string[] = [];
    for (let i = 0; i < localStorage.length; i++) {
      const key = localStorage.key(i);
      if (key && key.startsWith("dismissBanner_")) {
        keysToRemove.push(key);
      }
    }

    // Remove the keys
    keysToRemove.forEach((key) => localStorage.removeItem(key));

    // Update last cleanup timestamp
    localStorage.setItem(CLEANUP_KEY, now.toString());
  } catch (error) {
    console.error("Error cleaning up banner dismissals:", error);
  }
};

const outsideHourSettings = createResource({
  url: "helpdesk.helpdesk.doctype.hd_ticket.api.is_outside_check",
  debounce: 300,
  params: {
    ticket_name: props.ticketId,
  },
  auto: true,
});

// const bannerMsg = createResource({
//   url: "helpdesk.api.banner_msg.get_rendered_banner_msg",
//   params: {
//     ticket_id: props.ticketId,
//   },
//   auto: true,
// });

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
      toast.success(__("Ticket updated"));
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
    title: __("Close Ticket"),
    message: __("Are you sure you want to close this ticket?"),
    actions: [
      {
        label: __("Confirm"),
        variant: "solid",
        onClick(close: Function) {
          ticket.data.status = "Closed";
          setValue.submit(
            { fieldname: "status", value: "Closed" },
            {
              onSuccess: () => {
                toast.success(__("Ticket closed"));
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
  let items = [{ label: __("Tickets"), route: { name: "TicketsCustomer" } }];
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
const { startViewing, stopViewing } = useActiveViewers(props.ticketId);
onMounted(() => {
  startViewing(props.ticketId);
  document.title = props.ticketId;

  socket.on("helpdesk:ticket-update", ({ ticket_id }) => {
    if (ticket_id === props.ticketId) {
      ticket.reload();
    }
  });
});

onUnmounted(() => {
  stopViewing(props.ticketId);
  document.title = "Helpdesk";
  socket.off("helpdesk:ticket-update");
});
</script>
