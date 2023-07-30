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
          :theme="ticketStatusStore.statusColormapAgent[data.status]"
          variant="subtle"
        />
      </div>
    </template>
  </TopBar>
</template>

<script setup lang="ts">
import { computed } from "vue";
import dayjs from "dayjs";
import { Icon } from "@iconify/vue";
import { AGENT_PORTAL_TICKET_LIST } from "@/router";
import { copy } from "@/utils/clipboard";
import { useTicketStatusStore } from "@/stores/ticketStatus";
import TopBar from "@/components/TopBar.vue";
import { useTicket } from "./data";

const ticketStatusStore = useTicketStatusStore();
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
</script>
