<template>
  <Tabs
    :modelValue="activeTab"
    @update:modelValue="changeTabTo"
    class="flex flex-1 flex-col overflow-hidden"
  >
    <!-- the row carries the underline so it runs beneath the actions too -->
    <div
      class="flex shrink-0 items-center gap-2 border-b border-outline-gray-1 px-5"
    >
      <TabList size="md" class="flex-1 !border-b-0 py-1.5">
        <TabTrigger
          v-for="tab in tabs"
          :key="tab.value"
          :value="tab.value"
          :label="tab.label"
          :icon-left="tab.iconLeft"
        />
      </TabList>
      <TicketCallActions v-if="activeTab === 'call'" />
    </div>
    <TabPanel
      v-for="tab in tabs"
      :key="tab.value"
      :value="tab.value"
      class="min-h-0 flex-1 flex-col overflow-auto data-[state=active]:flex"
    >
      <TicketAnalyticsTab v-if="tab.value === 'analytics'" />
      <TicketTimeline
        v-else
        :ticket-id="String(ticket.doc?.name)"
        :tab="tab.value"
        :tab-label="tab.label"
        @email:reply="(e) => communicationAreaRef?.replyToEmail(e)"
      />
    </TabPanel>
  </Tabs>
  <!-- Comm Area -->
  <CommunicationArea
    ref="communicationAreaRef"
    :ticketId="String(ticket.doc?.name)"
    :to-emails="[ticket.doc?.raised_by]"
    :cc-emails="[]"
    :bcc-emails="[]"
    :key="ticket.doc?.name"
    @update="reloadTicketFeed(String(ticket.doc?.name))"
  />
</template>

<script setup lang="ts">
import CommunicationArea from "@/components/CommunicationArea.vue";
import {
  ActivityIcon,
  CommentIcon,
  EmailIcon,
  PhoneIcon,
} from "@/components/icons";
import TicketAnalyticsTab from "@/components/ticket-agent/analytics/TicketAnalyticsTab.vue";
import TicketCallActions from "@/components/ticket/TicketCallActions.vue";
import { useActiveTabManager } from "@/composables/useActiveTabManager";
import { reloadTicketFeed } from "@/composables/useTicket";
import { useTelephonyStore } from "@/stores/telephony";
import { TabObject, TicketSymbol } from "@/types";
import { TabList, TabPanel, TabTrigger, Tabs } from "frappe-ui";
import { storeToRefs } from "pinia";
import { computed, ComputedRef, inject, ref } from "vue";
import LucideChartNoAxesColumn from "~icons/lucide/chart-no-axes-column";
import TicketTimeline from "./timeline/TicketTimeline.vue";

const ticket = inject(TicketSymbol)!;

const communicationAreaRef = ref<InstanceType<typeof CommunicationArea> | null>(
  null
);
const telephonyStore = useTelephonyStore();
const { isCallingEnabled } = storeToRefs(telephonyStore);

const tabs: ComputedRef<TabObject[]> = computed(() => {
  const _tabs: TabObject[] = [
    {
      value: "activity",
      label: "Activity",
      iconLeft: ActivityIcon,
    },
    {
      value: "email",
      label: "Emails",
      iconLeft: EmailIcon,
    },
    {
      value: "comment",
      label: "Comments",
      iconLeft: CommentIcon,
    },
  ];

  if (isCallingEnabled.value) {
    _tabs.push({
      value: "call",
      label: "Calls",
      iconLeft: PhoneIcon,
    });
  }
  _tabs.push({
    value: "analytics",
    label: "Analytics",
    iconLeft: LucideChartNoAxesColumn,
  });
  return _tabs;
});

const { activeTab, changeTabTo } = useActiveTabManager(tabs);
</script>
