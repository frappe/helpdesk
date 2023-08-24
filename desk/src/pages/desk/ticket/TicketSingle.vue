<template>
  <div v-if="ticket.data" class="flex flex-col">
    <TopBar />
    <div class="flex grow overflow-hidden">
      <div class="flex grow flex-col">
        <PinnedComments />
        <ConversationBox class="grow" />
        <ResponseEditor />
      </div>
      <SideBar />
    </div>
  </div>
</template>

<script setup lang="ts">
import { onBeforeUnmount, onMounted, toRef } from "vue";
import { createResource, usePageMeta } from "frappe-ui";
import { emitter } from "@/emitter";
import { socket } from "@/socket";
import ConversationBox from "./ConversationBox.vue";
import PinnedComments from "./PinnedComments.vue";
import ResponseEditor from "./editor/ResponseEditor.vue";
import SideBar from "./SideBar.vue";
import TopBar from "./TopBar.vue";
import { useTicket } from "./data";

interface P {
  ticketId: string;
}

const props = defineProps<P>();
const ticketId = toRef(props, "ticketId");
const ticket = useTicket(ticketId.value);

createResource({
  url: "run_doc_method",
  params: {
    dt: "HD Ticket",
    dn: ticketId.value,
    method: "mark_seen",
  },
  auto: true,
});

emitter.on("update:ticket", () => ticket.value.reload());

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
      const shouldReload = !id || id == ticketId.value;
      if (shouldReload) ticket.value.reload();
    })
  )
);
onBeforeUnmount(() => {
  events.forEach((e) => socket.off(e));
  ticket.value = null;
});

usePageMeta(() => {
  return {
    title: ticket.value.data.subject,
  };
});
</script>
