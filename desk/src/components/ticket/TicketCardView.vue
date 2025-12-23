<template>
  <div class="flex-1">
    <div v-if="loading" class="flex items-center justify-center py-20">
      <LoadingIndicator :scale="10" />
    </div>
    <EmptyState 
      v-else-if="!rows.length" 
      :title="emptyTitle" 
      icon="layout-grid"
      class="py-20"
    />
    <div v-else class="flex flex-col gap-3">
      <div
        v-for="ticket in rows"
        :key="ticket.name"
        class="cursor-pointer border border-outline-gray-2 bg-surface-white p-4 transition-all duration-200 hover:border-outline-gray-3"
        style="box-shadow: 9px 4px 4px 0 rgba(0, 0, 0, 0.02);"
        :class="resolvedClass(ticket)"
        @click="handleCardClick(ticket)"
      >
        <div class="flex items-center gap-4">
          <input
            type="checkbox"
            class="mt-1 h-4 w-4 rounded-sm border border-outline-gray-3 text-ink-gray-8 focus:ring-2 focus:ring-outline-gray-3"
            @click.stop
            aria-label="Select ticket"
          />
          <div
            class="flex flex-shrink-0 items-center justify-center rounded-full text-sm font-semibold"
            style="width: 37px; height: 37px; aspect-ratio: 1 / 1;"
            :class="avatarClasses(ticket)"
          >
            {{ ticketInitials(ticket) }}
          </div>
          <div class="min-w-0 flex-1 space-y-3">
            <div class="flex flex-wrap items-center gap-2">
              <span
                v-if="isFirstResponseDue(ticket)"
                class="rounded-full border border-red-200 bg-red-50 px-2.5 py-1 text-xs font-semibold text-red-600"
              >
                First response due
              </span>
              <div class="flex min-w-0 flex-wrap items-baseline gap-2">
                <p class="line-clamp-1 text-base font-semibold text-ink-gray-9">
                  {{ ticket.subject || ticket.name }}
                </p>
                <span class="text-sm font-medium text-ink-gray-6">#{{ ticket.name }}</span>
              </div>
            </div>

            <div class="flex flex-wrap items-center gap-2 text-sm text-ink-gray-7">
              <div v-if="requesterName(ticket)" class="flex items-center gap-1.5">
                <LucideUser class="h-4 w-4" />
                <span class="truncate">{{ requesterName(ticket) }}</span>
              </div>
              <span
                v-if="requesterName(ticket) && ticket.creation"
                class="text-ink-gray-4"
                aria-hidden="true"
              >
                &bull;
              </span>
              <div v-if="ticket.creation" class="flex items-center gap-1.5">
                <LucideClock3 class="h-4 w-4" />
                <span>{{ createdText(ticket.creation) }}</span>
              </div>
              <span
                v-if="ticket.creation && ticket.resolution_by"
                class="text-ink-gray-4"
                aria-hidden="true"
              >
                &bull;
              </span>
              <div v-if="ticket.resolution_by" class="flex items-center gap-1.5">
                <LucideAlarmClock class="h-4 w-4" />
                <span>{{ dueText(ticket.resolution_by) }}</span>
              </div>
            </div>

            <div class="flex flex-wrap items-center gap-4 text-sm text-ink-gray-8">
              <Dropdown
                v-if="priorityOptions?.length"
                :options="priorityOptionsList(ticket)"
                placement="bottom-start"
              >
                <button
                  class="flex items-center gap-1.5 rounded-md px-0.5 py-1 text-ink-gray-9 transition-colors hover:text-ink-gray-8"
                  @click.stop
                >
                  <span class="h-2.5 w-2.5 rounded-full" :class="priorityMeta(ticket.priority).dot" />
                  <span class="font-medium" :class="priorityMeta(ticket.priority).text">
                    {{ ticket.priority || "No priority" }}
                  </span>
                  <LucideChevronDown class="h-3.5 w-3.5 text-ink-gray-6" />
                </button>
              </Dropdown>
              <div v-else class="flex items-center gap-1.5">
                <span class="h-2.5 w-2.5 rounded-full" :class="priorityMeta(ticket.priority).dot" />
                <span class="font-medium" :class="priorityMeta(ticket.priority).text">
                  {{ ticket.priority || "No priority" }}
                </span>
              </div>
              <Dropdown :options="statusOptionsList(ticket)" placement="bottom-start">
                <button
                  class="flex items-center gap-1.5 rounded-md px-0.5 py-1 text-ink-gray-9 transition-colors hover:text-ink-gray-8"
                  @click.stop
                >
                  <span class="h-2.5 w-2.5 rounded-full" :class="statusDot(ticket)" />
                  <span class="font-medium">{{ statusLabel(ticket) }}</span>
                  <LucideChevronDown class="h-3.5 w-3.5 text-ink-gray-6" />
                </button>
              </Dropdown>
              <div
                v-if="assigneeName(ticket)"
                class="inline-flex items-center gap-1.5 rounded-full border border-outline-gray-2 bg-surface-gray-1 px-2 py-0.5 text-xs font-medium text-ink-gray-8"
              >
                <LucideUsers class="h-3.5 w-3.5 text-ink-gray-6" />
                <span class="truncate">Assigned: {{ assigneeName(ticket) }}</span>
              </div>
              <div
                v-if="teamName(ticket)"
                class="inline-flex items-center gap-1.5 rounded-full border border-outline-gray-2 bg-surface-gray-1 px-2 py-0.5 text-xs font-medium text-ink-gray-8"
              >
                <LucideUsers class="h-3.5 w-3.5 text-ink-gray-6" />
                <span class="truncate">Team: {{ teamName(ticket) }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import EmptyState from "@/components/EmptyState.vue";
import { dayjs } from "@/dayjs";
import { useTicketStatusStore } from "@/stores/ticketStatus";
import { Dropdown, LoadingIndicator } from "frappe-ui";
import LucideAlarmClock from "~icons/lucide/alarm-clock";
import LucideChevronDown from "~icons/lucide/chevron-down";
import LucideClock3 from "~icons/lucide/clock-3";
import LucideUser from "~icons/lucide/user";
import LucideUsers from "~icons/lucide/users";

const props = withDefaults(
  defineProps<{
    rows: any[];
    loading?: boolean;
    emptyTitle?: string;
    statusOptions?: Array<{
      label: string;
      value: string;
      indicatorClass?: string;
      category?: string;
    }>;
    priorityOptions?: string[];
  }>(),
  {
    rows: () => [],
    loading: false,
    emptyTitle: "No Tickets Found",
    statusOptions: () => [],
    priorityOptions: () => [],
  }
);

const emit = defineEmits<{
  (e: "rowClick", ticketId: string): void;
  (e: "updateStatus", ticketId: string, value: string): void;
  (e: "updatePriority", ticketId: string, value: string): void;
}>();

const { getStatus } = useTicketStatusStore();

function statusMeta(row: any) {
  return getStatus(row?.status) || {};
}

function statusLabel(row: any) {
  return statusMeta(row)?.label_agent || row?.status;
}

const createdText = (value?: string) =>
  value ? `Created ${dayjs(value).fromNow()}` : "";

const dueText = (value?: string) =>
  value ? `Due ${dayjs(value).fromNow()}` : "";

function statusDot(row: any) {
  const meta = statusMeta(row);
  return meta?.parsed_color || "bg-ink-gray-4";
}

function ticketInitials(row: any) {
  const source =
    row?.customer ||
    row?.contact_name ||
    row?.contact ||
    row?.raised_by_name ||
    row?.subject ||
    row?.name ||
    "";
  const cleaned = String(source).trim();
  if (!cleaned) return "NA";
  return cleaned
    .split(/[\s@._-]+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase() || "")
    .join("") || "NA";
}

function requesterName(row: any) {
  return (
    row?.customer ||
    row?.contact_name ||
    row?.contact ||
    row?.raised_by_name ||
    row?.raised_by ||
    ""
  );
}

function assigneeName(row: any) {
  if (Array.isArray(row?.assignees) && row.assignees.length) {
    const primary = row.assignees[0];
    if (typeof primary === "string") return primary;
    return primary?.full_name || primary?.name || primary?.email || "";
  }
  // Fallback to _assign JSON (card API exposes this)
  if (row?._assign) {
    try {
      const parsed = JSON.parse(row._assign);
      if (Array.isArray(parsed) && parsed.length) {
        return parsed[0];
      }
    } catch (e) {
      // ignore JSON parse errors and fall through to other fields
    }
  }
  return row?.assigned_to || row?.owner || "";
}

function teamName(row: any) {
  return row?.agent_group || "";
}

function priorityMeta(priority?: string) {
  const value = String(priority || "").toLowerCase();
  if (value.includes("urgent") || value.includes("high")) {
    return { dot: "bg-red-600", text: "text-red-600" };
  }
  if (value.includes("medium")) {
    return { dot: "bg-purple-600", text: "text-purple-700" };
  }
  if (value.includes("low")) {
    return { dot: "bg-green-500", text: "text-green-600" };
  }
  return { dot: "bg-outline-gray-3", text: "text-ink-gray-9" };
}

function statusOptionsList(row: any) {
  return (props.statusOptions || []).map((opt) => ({
    label: opt.label,
    onClick: () => emit("updateStatus", row.name, opt.value),
  }));
}

function priorityOptionsList(row: any) {
  return (props.priorityOptions || []).map((opt) => ({
    label: opt,
    onClick: () => emit("updatePriority", row.name, opt),
  }));
}

function resolvedClass(row: any) {
  const meta = statusMeta(row);
  if (meta.category === "Resolved") {
    return "!bg-gray-50 !border-gray-200 opacity-70 !cursor-default hover:!shadow-sm";
  }
  return "";
}

function handleCardClick(ticket: any) {
  const ticketId = ticket.name || ticket;
  console.log("Card clicked, ticket ID:", ticketId);
  emit("rowClick", ticketId);
}

function avatarClasses(row: any) {
  const palette = [
    ["bg-indigo-100", "text-indigo-700"],
    ["bg-purple-100", "text-purple-700"],
    ["bg-amber-100", "text-amber-700"],
    ["bg-green-100", "text-green-700"],
    ["bg-blue-100", "text-blue-700"],
    ["bg-pink-100", "text-pink-700"],
  ];
  const base =
    row?.customer ||
    row?.contact_name ||
    row?.contact ||
    row?.raised_by_name ||
    row?.subject ||
    row?.name ||
    "";
  const hash = String(base)
    .split("")
    .reduce((acc, char) => acc + char.charCodeAt(0), 0);
  const [bg, text] = palette[hash % palette.length];
  return [bg, text].join(" ");
}

function isFirstResponseDue(row: any) {
  if (!row.response_by) return false;
  const responseBy = dayjs(row.response_by);
  const firstResponded = row.first_responded_on ? dayjs(row.first_responded_on) : null;
  // Show badge until first response is recorded, or if first response missed the SLA window.
  if (!firstResponded) return true;
  return firstResponded.isAfter(responseBy);
}
</script>
