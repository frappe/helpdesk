<template>
  <div v-if="cards.length">
    <div
      v-for="card in cards"
      :key="card.title"
      class="group flex min-h-7 items-center gap-2 leading-5"
    >
      <div class="w-[106px] shrink-0 truncate text-base text-ink-gray-5">
        {{ __(card.title) }}
      </div>
      <!-- 9px = field controls' 8px padding + 1px transparent border -->
      <div class="flex min-w-0 flex-1 items-center gap-1.5 ps-[9px]">
        <Badge
          variant="ghost"
          size="lg"
          :theme="badgeTheme[card.metric.color]"
          class="min-w-0 !px-0 !text-base font-semibold"
        >
          <span class="truncate">{{ cardValue(card) }}</span>
        </Badge>
        <Popover
          placement="bottom"
          :show="openCard === card.title"
          @update:show="(open: boolean) => (openCard = open ? card.title : null)"
        >
          <template #target>
            <LucideInfo
              class="size-3.5 shrink-0 cursor-pointer text-ink-gray-4 opacity-0 transition-opacity hover:text-ink-gray-6 group-hover:opacity-100"
              @mouseenter="openCard = card.title"
              @mouseleave="openCard = null"
            />
          </template>
          <template #body-main>
            <div class="flex min-w-[170px] flex-col gap-1.5 p-3 text-sm">
              <div
                v-for="row in cardDetails(card)"
                :key="row.label"
                class="flex items-baseline justify-between gap-8"
              >
                <span class="text-ink-gray-5">{{ __(row.label) }}</span>
                <span
                  class="font-medium tabular-nums"
                  :class="row.danger ? 'text-ink-red-6' : 'text-ink-gray-8'"
                >
                  {{ row.value }}
                </span>
              </div>
              <div
                v-if="card.metric.delayInWorkingHours"
                class="mt-0.5 border-t pt-1.5 text-xs text-ink-gray-4"
              >
                {{ __("Delay in working hours") }}
              </div>
            </div>
          </template>
        </Popover>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useSLA, type SLAMetric } from "@/composables/useSLA";
import { __ } from "@/translation";
import { TicketSymbol } from "@/types";
import { dateFormat } from "@/utils";
import { Badge, Popover } from "frappe-ui";
import { computed, inject, ref } from "vue";
import LucideInfo from "~icons/lucide/info";

interface SLACard {
  title: string;
  metric: SLAMetric;
  fulfilledLabel: string;
  actualLabel: string;
}

const ticket = inject(TicketSymbol)!;
const { firstResponse, resolution } = useSLA(ticket);

const openCard = ref<string | null>(null);

// Badge has no "purple" theme; its violet theme carries the purple ink tokens
const badgeTheme: Record<SLAMetric["color"], string> = {
  orange: "orange",
  green: "green",
  red: "red",
  blue: "blue",
  purple: "violet",
};

const cards = computed<SLACard[]>(() =>
  [
    {
      title: "First Response",
      metric: firstResponse.value,
      fulfilledLabel: "Fulfilled",
      actualLabel: "Responded on",
    },
    {
      title: "Resolution due",
      metric: resolution.value,
      fulfilledLabel: "Fulfilled",
      actualLabel: "Resolved on",
    },
  ].filter((card): card is SLACard => Boolean(card.metric))
);

function cardValue(card: SLACard): string {
  if (card.metric.state !== "fulfilled") return __(card.metric.value);
  if (!card.metric.fulfilledIn) return __(card.fulfilledLabel);
  return `${__(card.fulfilledLabel)} ${__("in")} ${card.metric.fulfilledIn}`;
}

function cardDetails(card: SLACard) {
  const metric = card.metric;
  const rows = [];
  if (metric.dueBy) {
    rows.push({ label: "Due by", value: fmt(metric.dueBy), danger: false });
  }
  if (metric.state === "hold") {
    rows.push({
      label: "On hold since",
      value: fmt(ticket.value.doc.on_hold_since as string),
      danger: false,
    });
  }
  if (metric.actual) {
    rows.push({
      label: card.actualLabel,
      value: fmt(metric.actual),
      danger: metric.state === "failed",
    });
  }
  if (metric.delay) {
    rows.push({ label: "Delay", value: metric.delay, danger: true });
  }
  if (metric.fulfilledIn) {
    rows.push({
      label: "Fulfilled in",
      value: metric.fulfilledIn,
      danger: false,
    });
  }
  return rows;
}

function fmt(date: string): string {
  return dateFormat(date, "MMM D, h:mm A");
}
</script>
