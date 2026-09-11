<template>
  <Tabs
    :modelValue="activeTab"
    :tabs="tabs"
    @update:modelValue="changeTabTo"
    class="[&_[role='tab']]:px-0 [&_[role='tablist']]:px-5 [&_[role='tablist']]:gap-7.5 [&_[role='tablist']]:flex-shrink-0 [&_[role='tabpanel'][data-state='active']]:flex-1"
  >
    <template #tab-panel="{ tab }">
      <TicketAnalyticsTab v-if="tab.value === 'analytics'" />
      <TicketTimeline
        v-else
        :ticket-id="String(ticket.doc?.name)"
        :tab="tab.value"
        :tab-label="tab.label"
        @email:reply="(e) => communicationAreaRef?.replyToEmail(e)"
      />
    </template>
  </Tabs>
  <!-- Comm Area -->
  <CommunicationArea
    ref="communicationAreaRef"
    :ticketId="String(ticket.doc?.name)"
    :to-emails="[ticket.doc?.raised_by]"
    :cc-emails="[]"
    :bcc-emails="[]"
    :key="ticket.doc?.name"
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
import { useActiveTabManager } from "@/composables/useActiveTabManager";
import { useTelephonyStore } from "@/stores/telephony";
import { TabObject, TicketSymbol } from "@/types";
import { Tabs } from "frappe-ui";
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
      icon: ActivityIcon,
    },
    {
      value: "email",
      label: "Emails",
      icon: EmailIcon,
    },
    {
      value: "comment",
      label: "Comments",
      icon: CommentIcon,
    },
  ];

  if (isCallingEnabled.value) {
    _tabs.push({
      value: "call",
      label: "Calls",
      icon: PhoneIcon,
    });
  }
  _tabs.push({
    value: "analytics",
    label: "Analytics",
    icon: LucideChartNoAxesColumn,
  });
  return _tabs;
});

const { activeTab, changeTabTo } = useActiveTabManager(tabs);
</script>
