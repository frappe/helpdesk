<template>
  <div v-if="ticket.data" class="flex flex-col">
    <TopBar
      :title="ticket.data.subject"
      :back-to="{ name: AGENT_PORTAL_TICKET_LIST }"
    >
      <template #bottom>
        <div class="flex items-center gap-1 text-base text-gray-600">
          <Tooltip :text="viaCustomerPortal ? textCustomerPortal : textEmail">
            <Icon
              :icon="viaCustomerPortal ? 'lucide:globe' : 'lucide:at-sign'"
              class="h-4 w-4"
            />
          </Tooltip>
          <Icon icon="lucide:dot" />
          <div class="cursor-copy" @click="copyId">
            # {{ ticket.data.name }}
          </div>
          <Icon icon="lucide:dot" />
          <Tooltip :text="dateLong"> Last modified {{ dateShort }} </Tooltip>
        </div>
      </template>
    </TopBar>
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
import { computed, onBeforeUnmount, onMounted, toRef } from "vue";
import { createResource } from "frappe-ui";
import { useClipboard } from "@vueuse/core";
import dayjs from "dayjs";
import { Icon } from "@iconify/vue";
import { AGENT_PORTAL_TICKET_LIST } from "@/router";
import { emitter } from "@/emitter";
import { socket } from "@/socket";
import { createToast } from "@/utils/toasts";
import TopBar from "@/components/TopBar.vue";
import ConversationBox from "./ConversationBox.vue";
import PinnedComments from "./PinnedComments.vue";
import ResponseEditor from "./editor/ResponseEditor.vue";
import SideBar from "./SideBar.vue";
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

const { copy } = useClipboard();
const date = computed(() =>
  dayjs(ticket.value.data.modified).tz(dayjs.tz.guess())
);
const dateLong = computed(() => date.value.format("dddd, MMMM D, YYYY h:mm A"));
const dateShort = computed(() => date.value.fromNow());
const textCustomerPortal = "Created via customer portal";
const textEmail = "Created via email";
const viaCustomerPortal = computed(() => ticket.value.data.via_customer_portal);

async function copyId() {
  await copy(ticket.value.data.name);

  createToast({
    title: "Copied to clipboard",
    icon: "check",
    iconClasses: "text-green-600",
  });
}

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
</script>
