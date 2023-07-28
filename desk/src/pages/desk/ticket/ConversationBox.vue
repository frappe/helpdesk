<template>
  <div class="flex flex-col overflow-hidden">
    <div
      v-if="isLoaded"
      ref="listElement"
      class="flex w-full flex-col items-center gap-4 overflow-auto"
    >
      <div class="content">
        <div v-for="c in conversations" :id="c.name" :key="c.name" class="mt-4">
          <CommunicationItem
            v-if="c.isCommunication"
            :content="c.content"
            :date="c.creation"
            :sender="c.sender.full_name"
            :sender-image="c.sender.image"
            :cc="c.cc"
            :bcc="c.bcc"
            :attachments="c.attachments"
          >
            <template #extra="{ content, cc, bcc }">
              <Dropdown :options="dropdownOptions(content, cc, bcc)">
                <Button
                  theme="gray"
                  variant="ouline"
                  class="opacity-0 group-hover:opacity-100"
                >
                  <template #icon>
                    <IconMoreHorizontal class="h-4 w-4" />
                  </template>
                </Button>
              </Dropdown>
            </template>
          </CommunicationItem>
          <CommentItem
            v-else
            :name="c.name"
            :content="c.content"
            :date="c.creation"
            :sender="c.sender"
            :is-pinned="c.is_pinned"
          />
        </div>
      </div>
    </div>
    <div v-else class="flex grow items-center justify-center">
      <LoadingIndicator class="w-5 text-gray-900" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onUnmounted, ref, watch } from "vue";
import { storeToRefs } from "pinia";
import { useScroll } from "@vueuse/core";
import { debounce, Button, Dropdown, LoadingIndicator } from "frappe-ui";
import dayjs from "dayjs";
import { orderBy, unionBy } from "lodash";
import { socket } from "@/socket";
import { useTicketStore } from "./data";
import CommunicationItem from "@/components/CommunicationItem.vue";
import CommentItem from "./CommentItem.vue";
import IconMoreHorizontal from "~icons/lucide/more-horizontal";
import IconReply from "~icons/lucide/reply";
import IconReplyAll from "~icons/lucide/reply-all";

type SocketData = {
  ticket_id: string;
};

const { editor, ticket } = useTicketStore();
const { focusedConversationItem } = storeToRefs(useTicketStore());
const listElement = ref(null);
const isCommunicationsLoaded = ref(false);
const isCommentsLoaded = ref(false);
const isLoaded = computed(
  () => isCommunicationsLoaded.value && isCommentsLoaded.value
);

watch(isLoaded, (v) => {
  if (v) scrollBottom();
});
watch(
  () => editor.isExpanded,
  () => scrollBottom()
);

ticket.getCommunications
  .submit()
  .then(() => (isCommunicationsLoaded.value = true));
ticket.getComments.submit().then(() => (isCommentsLoaded.value = true));

const ticketId = computed(() => ticket.doc.name);
const communications = computed(
  () => ticket.getCommunications.data?.message?.map(mapCommunication) || []
);
const comments = computed(() => ticket.getComments.data?.message || []);
const conversations = computed(() =>
  orderBy(unionBy(communications.value, comments.value), (c) =>
    dayjs(c.creation)
  )
);

function dropdownOptions(content: string, cc: string, bcc: string) {
  return [
    {
      label: "Reply",
      icon: IconReply,
      onClick: () => {
        editor.cc = [];
        editor.bcc = [];
        editor.content = quote(content);
        editor.isExpanded = true;
      },
    },
    {
      label: "Reply All",
      icon: IconReplyAll,
      onClick: () => {
        editor.cc = cc.split(",");
        editor.bcc = bcc.split(",");
        editor.content = quote(content);
        editor.isExpanded = true;
      },
    },
  ];
}

const scrollBottom = debounce(() => {
  const { y } = useScroll(listElement, { behavior: "smooth" });
  y.value = listElement.value.scrollHeight;
}, 500);

function mapCommunication(c) {
  return {
    ...c,
    isCommunication: true,
  };
}

function quote(s: string) {
  return `<blockquote>${s}</blockquote><br/>`;
}

socket.on("helpdesk:new-communication", (data: SocketData) => {
  if (data.ticket_id !== ticketId.value) return;
  ticket.getCommunications.reload().then(() => scrollBottom());
});

socket.on("helpdesk:new-ticket-comment", (data: SocketData) => {
  if (data.ticket_id !== ticketId.value) return;
  ticket.getComments.reload().then(() => scrollBottom());
});

socket.on("helpdesk:delete-ticket-comment", (data: SocketData) => {
  if (data.ticket_id !== ticketId.value) return;
  ticket.getComments.reload();
});

onUnmounted(() => {
  socket.off("helpdesk:new-communication");
  socket.off("helpdesk:new-ticket-comment");
  socket.off("helpdesk:delete-ticket-comment");
});

watch(focusedConversationItem, (id) => {
  const el = document.getElementById(id);
  el.scrollIntoView({ behavior: "smooth" });
});
</script>

<style scoped>
.content {
  width: 742px;
}
</style>
