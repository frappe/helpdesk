<template>
  <div v-if="cards.length" class="space-y-0.5">
    <div
<<<<<<< HEAD
      class="flex items-center ms-5 me-5 md:me-0 text-p-sm gap-3 text-[14px] mb-[13px]"
=======
      v-for="card in cards"
      :key="card.title"
      class="group flex min-h-7 items-center gap-2 leading-5"
>>>>>>> 865fdb4c (fix: reposition SLA layout)
    >
<<<<<<< HEAD
      <div class="w-[106px] shrink-0 truncate text-sm text-ink-gray-5">
        {{ __(card.title) }}
      </div>
<<<<<<< HEAD
      <!-- divider -->
      <div class="border-s border-outline-gray-2 h-[13px]" />
      <!-- First Response -->
      <div class="flex items-center gap-1">
        <span>First Response</span>

        <Tooltip
          :text="dateFormat(firstResponse.date, dateTooltipFormat)"
          :hover-delay="0.25"
          :placement="'top'"
=======
=======
      <FieldLabel :label="card.title" />
>>>>>>> 274271f8 (fix: polish side panel)
      <!-- 9px = field controls' 8px padding + 1px transparent border -->
      <div class="flex min-w-0 flex-1 items-center gap-1.5 ps-[9px]">
        <Badge
          variant="ghost"
          size="sm"
          :theme="badgeTheme[card.metric.color]"
<<<<<<< HEAD
          class="min-w-0 !px-0 !text-base font-semibold"
>>>>>>> 865fdb4c (fix: reposition SLA layout)
        >
          <span class="truncate">{{ cardValue(card) }}</span>
        </Badge>
=======
          class="min-w-0 !px-0 !text-base"
          :label="cardValue(card)"
        />
>>>>>>> 53284913 (fix: better SLA layout)
        <Popover
          placement="bottom"
          :show="openCard === card.title"
          @update:show="(open: boolean) => (openCard = open ? card.title : null)"
        >
          <template #target>
            <LucideInfo
              class="size-3.5 shrink-0 cursor-pointer text-ink-gray-6"
              @mouseenter="openCard = card.title"
              @mouseleave="openCard = null"
            />
          </template>
          <template #body-main>
            <div class="flex min-w-[170px] flex-col gap-2 p-3 text-sm">
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
            </div>
          </template>
        </Popover>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import FieldLabel from "@/components/FieldLabel.vue";
import { useSLA, type SLAMetric } from "@/composables/useSLA";
import { __ } from "@/translation";
import { TicketSymbol } from "@/types";
import { dateFormat } from "@/utils";
import { Badge, Popover } from "frappe-ui";
import { computed, inject, ref } from "vue";
import LucideInfo from "~icons/lucide/info";

<<<<<<< HEAD
const ticket = inject(TicketSymbol)!;

const timeFormat = {
  day: true,
  hour: true,
  minute: true,
};

// Cases:
// - if not first responded and response by is in future -> show due in
// - if first responded before response by -> show fulfilled in
// - if not first responded and response by is in past -> show overdue by
// - if first responded after response by -> show failed by
const firstResponse = computed(() => {
  if (ticket.value?.get?.loading) return { label: "", color: "gray" };
  if (
    !ticket.value.doc.first_responded_on &&
    dayjs().isBefore(dayjs(ticket.value.doc.response_by))
  ) {
    let responseBy = formatTimeShort(ticket.value.doc.response_by as string);
    return {
      label: `Due in ${responseBy}`,
      color: "orange",
    };
  } else if (
    dayjs(ticket.value.doc.first_responded_on).isBefore(
      dayjs(ticket.value.doc.response_by)
    )
  ) {
    let responseTime = ticket.value?.doc?.first_response_time;
    let format =
      responseTime <= 60
        ? {
            ...timeFormat,
            second: true,
          }
        : timeFormat;
    let fulfilled =
      responseTime != null
        ? formatTime(responseTime, format)
        : formatTimeShort(
            ticket.value.doc.first_responded_on as string,
            ticket.value.doc.creation
          );
    return {
      label: `Fulfilled in ${fulfilled}`,
      color: "green",
    };
  } else {
    if (!ticket.value.doc.first_responded_on) {
      let responseBy = formatTimeShort(
        String(new Date()),
        ticket.value.doc.response_by as string
      );
      return {
        label: `Overdue by ${responseBy}`,
        color: "red",
        date: ticket.value.doc.response_by,
      };
    }

    let failed = ticket.value?.doc?.first_response_failed_by
      ? formatTime(ticket.value.doc.first_response_failed_by, timeFormat)
      : formatTimeShort(
          ticket.value.doc.first_responded_on,
          ticket.value.doc.response_by
        );
    return {
      label: `Failed by ${failed}`,
      color: "red",
    };
  }
});

const resolutionBy = computed(() => {
  if (ticket.value?.get?.loading) return { label: "", color: "gray" };

  if (
    ticket.value.doc?.status_category === "Paused" &&
    ticket.value.doc?.on_hold_since &&
    dayjs(ticket.value.doc?.resolution_by).isAfter(
      dayjs(ticket.value.doc?.on_hold_since)
    )
  ) {
    return {
      label: `On Hold`,
      color: "blue",
    };
  } else if (
    !ticket.value.doc?.resolution_date &&
    dayjs().isAfter(dayjs(ticket.value.doc?.resolution_by))
  ) {
    let overdue = formatTimeShort(
      String(new Date()),
      ticket.value.doc?.resolution_by as string
    );

    return {
      label: `Overdue by ${overdue}`,
      color: "red",
      date: ticket.value.doc?.resolution_by,
    };
  } else if (
    !ticket.value.doc?.resolution_date &&
    dayjs().isBefore(dayjs(ticket.value.doc?.resolution_by))
  ) {
    let resolutionBy = formatTimeShort(
      ticket.value.doc?.resolution_by as string
    );
    return {
      label: `Due in ${resolutionBy}`,
      color: "purple",
    };
  } else if (
    dayjs(ticket.value.doc?.resolution_date).isBefore(
      dayjs(ticket.value.doc?.resolution_by)
    )
  ) {
    let resolutionTime = ticket.value?.doc?.resolution_time;
    let format =
      resolutionTime <= 60
        ? {
            ...timeFormat,
            second: true,
          }
        : timeFormat;
    let fulfilled =
      resolutionTime != null
        ? formatTime(resolutionTime, format)
        : formatTimeShort(
            ticket.value.doc?.resolution_date as string,
            ticket.value.doc?.creation
          );
    return {
      label: `Fulfilled in ${fulfilled}`,
      color: "green",
    };
  } else {
    let failed = ticket.value.doc?.resolution_failed_by
      ? formatTime(ticket.value.doc?.resolution_failed_by, timeFormat)
      : formatTimeShort(
          ticket.value.doc?.resolution_by,
          ticket.value.doc?.resolution_date
        );
    return {
      label: `Failed by ${failed}`,
      color: "red",
    };
  }
});

function formatTimeShort(date: string, end?: string): string {
  if (!end) {
    end = dayjs().toString();
  }
  let _date = dayjs(date);
  let duration = dayjs.duration(_date.diff(dayjs(end)));

  let years = duration.years();
  let months = duration.months();
  let days = duration.days();
  let hours = duration.hours();
  let minutes = duration.minutes();

  if (years > 0) {
    return `${years}y ${months}mo`;
  } else if (months > 0) {
    return `${months}mo ${days}d`;
  } else if (days > 0) {
    return `${days}d ${hours}h`;
  } else if (hours > 0) {
    return `${hours}h ${minutes}m`;
  } else {
    return `${minutes}m`;
  }
=======
interface SLACard {
  title: string;
  metric: SLAMetric;
  fulfilledLabel: string;
  actualLabel: string;
>>>>>>> 865fdb4c (fix: reposition SLA layout)
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
      title: "Resolution",
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
    rows.push({
      label: metric.delayInWorkingHours ? "Delay (working hours)" : "Delay",
      value: metric.delay,
      danger: true,
    });
    if (metric.calendarDelay) {
      rows.push({
        label: "Delay (total)",
        value: `+${metric.calendarDelay}`,
        danger: true,
      });
    }
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
