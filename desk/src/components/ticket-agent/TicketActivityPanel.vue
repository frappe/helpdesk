<template>
  <div
    ref="panelRef"
    class="relative flex min-h-0 flex-1 flex-col"
    :style="{ '--composer-reserve': `${composerHeight}px` }"
  >
    <Tabs
      :modelValue="activeTab"
      :tabs="tabs"
      @update:modelValue="changeTabTo"
      size="md"
      class="flex-1 overflow-hidden [&_[role='tablist']]:px-5 [&_[role='tablist']]:py-1.5 [&_[role='tablist']]:flex-shrink-0 [&_[role='tabpanel'][data-state='active']]:flex-1 [&_[role='tabpanel'][data-state='active']]:flex [&_[role='tabpanel'][data-state='active']]:flex-col [&_[role='tabpanel'][data-state='active']]:min-h-0"
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
    <!-- The composer floats over the thread instead of taking a row in it, so
         opening or resizing it never reflows the timeline. -->
    <div ref="composerRef" class="absolute inset-x-0 bottom-0 z-10">
      <CommunicationArea
        ref="communicationAreaRef"
        :ticketId="String(ticket.doc?.name)"
        :to-emails="[ticket.doc?.raised_by]"
        :key="ticket.doc?.name"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import CommunicationArea from "@/components/communication-area/CommunicationArea.vue";
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
import { useElementSize } from "@vueuse/core";
import { Tabs } from "frappe-ui";
import { storeToRefs } from "pinia";
import { computed, ComputedRef, inject, ref, useTemplateRef, watch } from "vue";
import LucideChartNoAxesColumn from "~icons/lucide/chart-no-axes-column";
import TicketTimeline from "./timeline/TicketTimeline.vue";

const ticket = inject(TicketSymbol)!;

const communicationAreaRef = ref<InstanceType<typeof CommunicationArea> | null>(
  null
);
const panelRef = useTemplateRef<HTMLElement>("panelRef");
const composerRef = useTemplateRef<HTMLElement>("composerRef");
const { height: composerHeight } = useElementSize(composerRef);

watch(
  composerHeight,
  (height, previous) => {
    if (!previous) return;
    const scroller = panelRef.value?.querySelector<HTMLElement>(
      "[role='tabpanel'][data-state='active'] .activity-timeline"
    );
    if (scroller) scroller.scrollTop -= height - previous;
  },
  { flush: "post" }
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
