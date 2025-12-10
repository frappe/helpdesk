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
        class="rounded-lg border border-outline-gray-2 bg-surface-white p-6 shadow-sm transition-all duration-200 hover:border-outline-gray-3 hover:shadow-md"
        :class="resolvedClass(ticket)"
      >
        <div class="flex items-start justify-between gap-6">
          <div class="flex min-w-0 flex-1 flex-col gap-4">
            <div class="flex flex-col gap-3">
              <div class="flex items-center gap-2">
                <span
                  v-if="isFirstResponseDue(ticket)"
                  class="w-fit rounded-full bg-red-50 px-3 py-1.5 text-xs font-semibold text-red-600"
                >
                  First response due
                </span>
                <span class="text-xs font-medium text-ink-gray-5">#{{ ticket.name }}</span>
              </div>
              <button
                class="text-left text-lg font-semibold text-ink-gray-9 hover:text-ink-gray-7 transition-colors line-clamp-2"
                @click="$emit('rowClick', ticket.name)"
              >
                {{ ticket.subject || ticket.name }}
              </button>
            </div>
            <div class="flex flex-wrap items-center gap-x-4 gap-y-2">
              <div class="flex items-center gap-2">
                <span class="text-xs font-medium text-ink-gray-6">Status:</span>
                <Badge
                  v-if="statusLabel(ticket)"
                  :label="statusLabel(ticket)"
                  variant="subtle"
                  :theme="statusTheme(ticket)"
                  class="text-xs font-medium"
                />
              </div>
              <div v-if="ticket.priority" class="flex items-center gap-2">
                <span class="text-xs font-medium text-ink-gray-6">Priority:</span>
                <Badge
                  :label="ticket.priority"
                  variant="outline"
                  theme="gray"
                  class="text-xs font-medium"
                />
              </div>
            </div>
            <div class="flex flex-wrap gap-4 text-sm text-ink-gray-6">
              <div v-if="ticket.customer" class="flex items-center gap-1.5">
                <LucideUser class="h-4 w-4" />
                <span class="truncate">{{ ticket.customer }}</span>
              </div>
              <div
                v-if="ticket.assignees?.length"
                class="flex items-center gap-1.5"
              >
                <LucideUsers class="h-4 w-4" />
                <MultipleAvatar
                  :avatars="ticket.assignees"
                  hide-name
                  class="h-6"
                />
              </div>
              <div v-if="ticket.creation" class="flex items-center gap-1.5">
                <LucideClock3 class="h-4 w-4" />
                <span>{{ createdText(ticket.creation) }}</span>
              </div>
              <div v-if="ticket.resolution_by" class="flex items-center gap-1.5">
                <LucideAlarmClock class="h-4 w-4" />
                <span>{{ dueText(ticket.resolution_by) }}</span>
              </div>
            </div>
          </div>
          <div class="flex flex-col items-stretch gap-2.5">
            <Dropdown :options="statusOptionsList(ticket)" placement="bottom-end">
              <button
                class="group flex items-center justify-between gap-3 rounded-lg border border-outline-gray-2 bg-surface-white px-3.5 py-2.5 text-left shadow-sm transition-all hover:border-outline-gray-3 hover:shadow focus:outline-none focus:ring-2 focus:ring-gray-200"
              >
                <div class="flex items-center gap-2.5 overflow-hidden">
                  <span
                    class="h-2.5 w-2.5 rounded-full flex-shrink-0"
                    :class="statusDot(ticket)"
                  />
                  <span class="truncate text-sm font-medium text-ink-gray-9">
                    {{ statusLabel(ticket) }}
                  </span>
                </div>
                <LucideChevronDown class="h-4 w-4 text-ink-gray-6 flex-shrink-0 transition-transform group-hover:text-ink-gray-8" />
              </button>
            </Dropdown>
            <Dropdown
              v-if="priorityOptions?.length"
              :options="priorityOptionsList(ticket)"
              placement="bottom-end"
            >
              <button
                class="group flex items-center justify-between gap-3 rounded-lg border border-outline-gray-2 bg-surface-white px-3.5 py-2.5 text-left shadow-sm transition-all hover:border-outline-gray-3 hover:shadow focus:outline-none focus:ring-2 focus:ring-gray-200"
              >
                <div class="flex items-center gap-2.5 overflow-hidden">
                  <LucideFlag class="h-4 w-4 text-ink-gray-6 flex-shrink-0" />
                  <span class="truncate text-sm font-medium text-ink-gray-9">
                    {{ ticket.priority || "No priority" }}
                  </span>
                </div>
                <LucideChevronDown class="h-4 w-4 text-ink-gray-6 flex-shrink-0 transition-transform group-hover:text-ink-gray-8" />
              </button>
            </Dropdown>
            <button
              class="flex items-center justify-center gap-2 rounded-lg px-3.5 py-2.5 text-sm font-medium text-ink-gray-7 transition-colors hover:bg-surface-gray-1 hover:text-ink-gray-9"
              @click="$emit('rowClick', ticket.name)"
            >
              <span>View details</span>
              <LucideArrowRight class="h-4 w-4" />
            </button>
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
import { Badge, Button, Dropdown, LoadingIndicator } from "frappe-ui";
import MultipleAvatar from "@/components/MultipleAvatar.vue";
import { withDefaults } from "vue";
import LucideAlarmClock from "~icons/lucide/alarm-clock";
import LucideArrowRight from "~icons/lucide/arrow-right";
import LucideChevronDown from "~icons/lucide/chevron-down";
import LucideClock3 from "~icons/lucide/clock-3";
import LucideFlag from "~icons/lucide/flag";
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

function statusTheme(row: any) {
  const category = statusMeta(row)?.category;
  if (category === "Resolved") return "green";
  if (category === "Paused") return "blue";
  if (category === "Overdue") return "red";
  return "orange";
}

const createdText = (value?: string) =>
  value ? `Created ${dayjs(value).fromNow()}` : "";

const dueText = (value?: string) =>
  value ? `Due ${dayjs(value).fromNow()}` : "";

function statusDot(row: any) {
  const meta = statusMeta(row);
  return meta?.parsed_color || "bg-ink-gray-4";
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
    return "!bg-gray-50 !border-gray-200 opacity-70 cursor-default hover:!shadow-sm";
  }
  return "cursor-pointer";
}

function isFirstResponseDue(row: any) {
  if (!row.response_by) return false;
  const now = dayjs();
  const responseBy = dayjs(row.response_by);
  const firstResponded = row.first_responded_on ? dayjs(row.first_responded_on) : null;
  if (firstResponded) {
    return firstResponded.isAfter(responseBy);
  }
  return responseBy.isBefore(now);
}
</script>

