<template>
  <div
    ref="panelRef"
    class="relative flex min-h-0 flex-1 flex-col"
    :style="{ '--composer-reserve': `${composerHeight}px` }"
  >
    <Tabs
      :modelValue="tabIndex"
      :tabs="tabs"
      @update:modelValue="changeTabTo"
      class="[&_[role='tab']]:px-0 [&_[role='tablist']]:px-5 [&_[role='tablist']]:gap-7.5 [&_[role='tablist']]:flex-shrink-0 [&_[role='tabpanel'][data-state='active']]:flex-1"
    >
      <template #tab-panel="{ tab }">
        <TicketAnalyticsTab v-if="tab.name === 'analytics'" />
        <TicketTimeline
          v-else
          :ticket-id="String(ticket.doc?.name)"
          :tab="tab.name"
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

// The timeline is bottom-anchored (flex-col-reverse), so reserving room for a
// taller composer shoves the thread up. Scroll back by the same amount to hold
// it still — except on first render, where the reserve appears with the pill.
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
      name: "activity",
      label: "Activity",
      icon: ActivityIcon,
    },
    {
      name: "email",
      label: "Emails",
      icon: EmailIcon,
    },
    {
      name: "comment",
      label: "Comments",
      icon: CommentIcon,
    },
  ];

  if (isCallingEnabled.value) {
    _tabs.push({
      name: "call",
      label: "Calls",
      icon: PhoneIcon,
    });
  }
  _tabs.push({
    name: "analytics",
    label: "Analytics",
    icon: LucideChartNoAxesColumn,
  });
  return _tabs;
});

const { tabIndex, changeTabTo } = useActiveTabManager(tabs);
</script>
