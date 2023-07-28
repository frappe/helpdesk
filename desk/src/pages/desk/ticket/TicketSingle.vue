<template>
  <div v-if="isResLoaded" class="flex flex-col">
    <TopBar
      :title="ticket.doc?.subject"
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
            # {{ ticket.doc?.name }}
          </div>
          <Icon icon="lucide:dot" />
          <Tooltip :text="dateLong"> Last modified {{ dateShort }} </Tooltip>
        </div>
      </template>
      <template #right>
        <Button label="Change team" theme="gray" variant="solid">
          <template #prefix>
            <Icon icon="lucide:users" />
          </template>
        </Button>
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
import { computed, onUnmounted, ref } from "vue";
import { useClipboard } from "@vueuse/core";
import { Button } from "frappe-ui";
import dayjs from "dayjs";
import { Icon } from "@iconify/vue";
import { AGENT_PORTAL_TICKET_LIST } from "@/router";
import { useConfigStore } from "@/stores/config";
import { createToast } from "@/utils/toasts";
import TopBar from "@/components/TopBar.vue";
import { useTicketStore } from "./data";
import ConversationBox from "./ConversationBox.vue";
import PinnedComments from "./PinnedComments.vue";
import ResponseEditor from "./editor/ResponseEditor.vue";
import SideBar from "./SideBar.vue";

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
