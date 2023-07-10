<template>
  <div v-if="isResLoaded" class="flex flex-col">
    <TopBar
      :title="ticket.doc?.subject"
      :back-to="{ name: AGENT_PORTAL_TICKET_LIST }"
    >
      <template #bottom>
        <div class="flex items-center gap-1 text-base text-gray-600">
          <Tooltip :text="viaCustomerPortal ? textCustomerPortal : textEmail">
            <component
              :is="viaCustomerPortal ? IconGlobe : IconAtSign"
              class="h-4 w-4"
            />
          </Tooltip>
          <IconDot />
          <div class="cursor-copy" @click="copyId">
            # {{ ticket.doc?.name }}
          </div>
          <IconDot />
          <Tooltip :text="dateLong"> Last modified {{ dateShort }} </Tooltip>
        </div>
      </template>
    </TopBar>
    <div class="flex grow overflow-hidden">
      <div class="flex grow flex-col">
        <ConversationBox class="grow" />
        <ResponseEditor />
      </div>
      <SideBar />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, onUnmounted } from "vue";
import { useClipboard } from "@vueuse/core";
import dayjs from "dayjs";
import { AGENT_PORTAL_TICKET_LIST } from "@/router";
import { useConfigStore } from "@/stores/config";
import { createToast } from "@/utils/toasts";
import TopBar from "@/components/TopBar.vue";
import { useTicketStore } from "./data";
import ConversationBox from "./ConversationBox.vue";
import ResponseEditor from "./editor/ResponseEditor.vue";
import SideBar from "./SideBar.vue";
import IconAtSign from "~icons/lucide/at-sign";
import IconDot from "~icons/lucide/dot";
import IconGlobe from "~icons/lucide/globe";

const props = defineProps({
  ticketId: {
    type: String,
    required: true,
  },
});
const { copy } = useClipboard();
const configStore = useConfigStore();
const { init, deinit, ticket } = useTicketStore();
const isResLoaded = ref(false);
const date = computed(() => dayjs(ticket.doc?.modified).tz(dayjs.tz.guess()));
const dateShort = computed(() => date.value.fromNow());
const dateLong = computed(() => date.value.format("dddd, MMMM D, YYYY h:mm A"));
const viaCustomerPortal = computed(() => ticket.doc?.via_customer_portal);
const textEmail = "Created via email";
const textCustomerPortal = "Created via customer portal";

async function copyId() {
  await copy(ticket.doc?.name);

  createToast({
    title: "Copied to clipboard",
    icon: "check",
    iconClasses: "text-green-600",
  });
}

init(parseInt(props.ticketId)).then(() => {
  configStore.setTitle(ticket.doc?.subject);
  ticket.markSeen.submit();
  isResLoaded.value = true;
});

onUnmounted(() => {
  deinit();
  configStore.setTitle();
});
</script>
