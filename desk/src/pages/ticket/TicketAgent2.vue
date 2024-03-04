<template>
  <div v-if="ticket.data" class="flex flex-col">
    <TicketBreadcrumbs parent="TicketsAgent">
      <template #right>
        <TicketAgentActions />
      </template>
    </TicketBreadcrumbs>
    <div class="flex grow overflow-auto">
      <div class="flex grow flex-col">
        <TicketPinnedComments @focus="(v) => (focus = v)" />
        <TicketConversation class="grow" :focus="focus">
          <template #communication-top-right="{ message }">
            <Button
              theme="gray"
              variant="ghost"
              @click="
                () => {
                  isExpanded = true;
                  mode = Mode.Response;
                  $nextTick(() =>
                    $refs.editor.editor
                      .chain()
                      .clearContent()
                      .insertContent(message)
                      .focus('all')
                      .setBlockquote()
                      .insertContentAt(0, { type: 'paragraph' })
                      .focus('start')
                      .run()
                  );
                }
              "
            >
              <template #icon>
                <Icon icon="lucide:reply" />
              </template>
            </Button>
          </template>
        </TicketConversation>
        <span class="m-5">
          <CommunicationArea
            ref="editor"
            v-model="ticket"
            v-model:attachments="attachments"
            v-model:content="content"
            v-model:expand="isExpanded"
            v-model:reload="reload_email"
            :mentions="agentStore.dropdown"
            :placeholder="placeholder"
            autofocus
            @clear="() => clear()"
          >
          </CommunicationArea>
        </span>
      </div>
      <TicketAgentSidebar />
    </div>
    <TicketCannedResponses
      v-model="showCannedResponses"
      @select="
        (content) => {
          $refs.editor.editor.commands.clearContent();
          $refs.editor.editor.commands.insertContent(content);
        }
      "
    />
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, provide, ref } from "vue";
import {
  createResource,
  usePageMeta,
  Button,
  FormControl,
  TabButtons,
} from "frappe-ui";
import { Icon } from "@iconify/vue";
import { emitter } from "@/emitter";
import { socket } from "@/socket";
import { useAgentStore } from "@/stores/agent";
import { useError } from "@/composables/error";
import TicketAgentActions from "./TicketAgentActions.vue";
import TicketAgentSidebar from "./TicketAgentSidebar.vue";
import TicketBreadcrumbs from "./TicketBreadcrumbs.vue";
import TicketCannedResponses from "./TicketCannedResponses.vue";
import TicketConversation from "./TicketConversation.vue";
import TicketPinnedComments from "./TicketPinnedComments.vue";
import { CommunicationArea } from "@/components/";
import { ITicket } from "./symbols";

interface P {
  ticketId: string;
}

enum Mode {
  Comment = "Comment",
  Response = "Response",
}

const reload_email = ref(false);

const props = defineProps<P>();
const agentStore = useAgentStore();
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
const placeholder = "Compose a comment / reply";
const content = ref("");
const attachments = ref([]);
const isExpanded = ref(false);
const cc = ref("");
const bcc = ref("");
const focus = ref("");
const showCannedResponses = ref(false);

createResource({
  url: "run_doc_method",
  params: {
    dt: "HD Ticket",
    dn: props.ticketId,
    method: "mark_seen",
  },
  auto: true,
});

emitter.on("update:ticket", () => ticket.reload());

const comment = createResource({
  url: "run_doc_method",
  debounce: 300,
  makeParams: () => ({
    dt: "HD Ticket",
    dn: props.ticketId,
    method: "new_comment",
    args: {
      content: content.value,
    },
  }),
  onSuccess: () => {
    clear();
    emitter.emit("update:ticket");
  },
  onError: useError({ title: "Error adding comment" }),
});

const response = createResource({
  url: "run_doc_method",
  debounce: 300,
  makeParams: () => ({
    dt: "HD Ticket",
    dn: props.ticketId,
    method: "reply_via_agent",
    args: {
      attachments: attachments.value.map((x) => x.name),
      cc: cc.value,
      bcc: bcc.value,
      message: content.value,
    },
  }),
  onSuccess: () => {
    clear();
    emitter.emit("update:ticket");
  },
});

const resource = computed(() => {
  return {
    Comment: comment,
    Response: response,
  }[mode.value];
});

function clear() {
  editor.value.editor.commands.clearContent(true);
  isExpanded.value = false;
  cc.value = "";
  bcc.value = "";
}

const events = [
  "helpdesk:new-communication",
  "helpdesk:new-ticket-comment",
  "helpdesk:delete-ticket-comment",
  "helpdesk:ticket-update",
  "helpdesk:update-ticket-assignee",
  "helpdesk:ticket-assignee-update",
];

onMounted(() =>
  events.forEach((e) =>
    socket.on(e, (d) => {
      const id = d.name || d.id;
      const shouldReload = !id || id == props.ticketId;
      if (shouldReload) ticket.reload();
    })
  )
);
onBeforeUnmount(() => events.forEach((e) => socket.off(e)));

usePageMeta(() => {
  return {
    title: ticket.data?.subject,
  };
});
</script>
