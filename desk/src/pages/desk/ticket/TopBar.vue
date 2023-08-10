<template>
  <TopBar :title="data.subject" :back-to="{ name: AGENT_PORTAL_TICKET_LIST }">
    <template #bottom>
      <div class="flex items-center gap-1 text-base text-gray-600">
        <Tooltip :text="sourceText">
          <Icon :icon="sourceIcon" class="h-4 w-4" />
        </Tooltip>
        <Icon icon="lucide:dot" />
        <div class="cursor-copy" @click="copy(data.name)">
          # {{ data.name }}
        </div>
        <Icon icon="lucide:dot" />
        <Tooltip :text="dateLong"> Last modified {{ dateShort }} </Tooltip>
        <Icon icon="lucide:dot" />
        <Badge
          :label="data.status"
          :theme="ticketStatusStore.colorMapAgent[data.status]"
          variant="subtle"
        />
      </div>
    </template>
    <template #right>
      <Autocomplete
        :options="agentStore.dropdown"
        :value="
          assignedTo
            ? {
                label: assignedTo?.full_name,
                value: assignedTo?.name,
              }
            : null
        "
        placeholder="Assign an agent"
        @change="assignAgent($event.value)"
      >
        <template #prefix>
          <Avatar
            v-if="assignedTo"
            class="mr-2"
            :label="assignedTo?.full_name"
            :image="assignedTo?.user_image"
          />
        </template>
        <template #item-prefix="{ option }">
          <Avatar
            class="mr-2"
            :label="userStore.getUser(option.value)?.full_name"
            :image="userStore.getUser(option.value)?.user_image"
          />
        </template>
      </Autocomplete>
    </template>
  </TopBar>
</template>

<script setup lang="ts">
import { computed } from "vue";
import dayjs from "dayjs";
import { createResource, Autocomplete, Avatar } from "frappe-ui";
import { Icon } from "@iconify/vue";
import { AGENT_PORTAL_TICKET_LIST } from "@/router";
import { emitter } from "@/emitter";
import { copy } from "@/utils/clipboard";
import { createToast } from "@/utils/toasts";
import { useAgentStore } from "@/stores/agent";
import { useTicketStatusStore } from "@/stores/ticketStatus";
import { useUserStore } from "@/stores/user";
import TopBar from "@/components/TopBar.vue";
import { useTicket } from "./data";

const agentStore = useAgentStore();
const ticketStatusStore = useTicketStatusStore();
const userStore = useUserStore();
const ticket = useTicket();
const data = computed(() => ticket.value.data);
const date = computed(() => dayjs(data.value.modified).tz(dayjs.tz.guess()));
const dateLong = computed(() => date.value.format("dddd, MMMM D, YYYY h:mm A"));
const dateShort = computed(() => date.value.fromNow());
const viaCustomerPortal = computed(() => data.value.via_customer_portal);
const sourceText = computed(() =>
  viaCustomerPortal.value ? "Created via customer portal" : "Created via email"
);
const sourceIcon = computed(() =>
  viaCustomerPortal.value ? "lucide:globe" : "lucide:at-sign"
);
const assignedTo = computed(() => {
  const assignJson = JSON.parse(data.value._assign);
  const arr = Array.isArray(assignJson) ? assignJson : [];
  const user = arr.slice(-1).pop();
  return userStore.getUser(user);
});

function assignAgent(agent: string) {
  createResource({
    url: "run_doc_method",
    params: {
      dt: "HD Ticket",
      dn: data.value.name,
      method: "assign_agent",
      args: {
        agent,
      },
    },
    auto: true,
    onSuccess: () => {
      emitter.emit("update:ticket");
      createToast({
        title: `Ticket assigned to ${agent}`,
        icon: "check",
        iconClasses: "text-green-600",
      });
    },
  });
}
</script>
