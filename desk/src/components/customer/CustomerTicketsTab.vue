<template>
  <div class="flex flex-col">
    <!-- Filter bar -->
    <div class="flex items-center justify-between gap-3 py-3">
      <FormControl
        v-model="search"
        :placeholder="__('Search tickets')"
        class="w-56"
      >
        <template #prefix>
          <LucideSearch class="h-4 w-4 text-ink-gray-4" />
        </template>
      </FormControl>

      <div class="flex items-center gap-2">
        <Link
          v-for="filter in filterFields"
          :key="filter.key"
          v-model="filters[filter.key]"
          :placeholder="filter.placeholder"
          :doctype="filter.doctype"
          :filters="filter.filters"
        />
      </div>
    </div>

    <!-- Table -->
    <div class="border-gray-200 overflow-hidden">
      <!-- Header -->
      <div
        class="grid items-center border-b border-gray-200 px-4 py-2 text-xs font-medium text-ink-gray-5"
        :style="gridTemplateStyle"
      >
        <div
          v-for="col in columns"
          :key="col.key"
          class="group flex items-center gap-1 select-none text-ink-gray-5"
          :class="col.sortable ? 'hover:text-ink-gray-8' : ''"
          @click="handleSortClick(col)"
        >
          {{ col.label }}
          <LucideArrowUpDown
            v-if="col.sortable"
            class="h-3 w-3 transition-opacity"
            :class="
              sort.field === col.key
                ? 'opacity-100 text-ink-gray-7'
                : 'opacity-0 group-hover:opacity-60'
            "
          />
        </div>
      </div>

      <!-- Loading -->
      <template v-if="ticketsListResource.loading">
        <div class="py-16 text-center text-sm text-ink-gray-4">
          <p>HELLOOOO</p>
          <LoadingIndicator :scale="10" />
        </div>
      </template>
      <!-- Empty -->
      <div
        v-else-if="
          !ticketsListResource.data?.length && !ticketsListResource.loading
        "
        class="py-16 text-center text-sm text-ink-gray-4"
      >
        {{ __("No tickets found.") }}
      </div>
      <!-- Rows -->
      <template v-else>
        <div
          v-for="(ticket, i) in ticketsListResource.data"
          :key="ticket.name"
          class="grid items-center px-4 py-3 text-sm text-ink-gray-8 cursor-pointer hover:bg-surface-gray-1 transition-colors"
          :class="
            i !== ticketsListResource?.data?.length - 1 &&
            'border-b border-gray-200'
          "
          :style="gridTemplateStyle"
        >
          <!-- ID -->
          <div class="text-ink-gray-6 font-base">{{ ticket.name }}</div>

          <!-- Subject -->
          <div class="truncate font-medium max-w-[90%]">
            {{ ticket.subject }}
          </div>

          <!-- Status -->
          <div class="flex items-center gap-1.5">
            <IndicatorIcon :class="ticket.statusColor" />
            <span>{{ ticket.status }}</span>
          </div>

          <!-- Priority -->
          <div class="flex items-center gap-1.5">
            <span>{{ ticket.priority }}</span>
          </div>

          <!-- First Response -->
          <div class="text-ink-gray-6">
            {{ dayjsLocal(ticket.response_by).fromNow() }}
          </div>

          <!-- Resolution -->
          <div class="text-ink-gray-6">
            {{ dayjsLocal(ticket.resolution_by).fromNow() }}
          </div>

          <!-- Assigned To -->
          <div class="flex items-center gap-2">
            <MultipleAvatar :avatars="ticket._assign" size="xs" />
          </div>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import { IndicatorIcon } from "@/components/icons";
import { useTicketStatusStore } from "@/stores/ticketStatus";
import { __ } from "@/translation";
import { CustomerResourceSymbol, ListResource } from "@/types";
import { HDTicket } from "@/types/doctypes";
import { watchDebounced } from "@vueuse/core";
import {
  createListResource,
  dayjsLocal,
  FormControl,
  LoadingIndicator,
} from "frappe-ui";
import { Link } from "frappe-ui/frappe";
import { computed, inject, reactive, ref } from "vue";
import LucideSearch from "~icons/lucide/search";
import MultipleAvatar from "../MultipleAvatar.vue";

const customer = inject(CustomerResourceSymbol)!;

const search = ref("");
const sort = reactive<{ field: string | null; order: "asc" | "desc" }>({
  field: null,
  order: "asc",
});
const filters = reactive<Record<string, string>>({
  status: "",
  priority: "",
  contact: "",
});

const gridTemplateStyle =
  "grid-template-columns: 6rem 1fr 8rem 7rem 8rem 8rem 9rem";

type Column = {
  key: string;
  label: string;
  sortable: boolean;
};
const columns: Column[] = [
  { key: "name", label: __("Ticket ID"), sortable: true },
  { key: "subject", label: __("Subject"), sortable: true },
  { key: "status", label: __("Status"), sortable: true },
  { key: "priority", label: __("Priority"), sortable: true },
  { key: "response_by", label: __("First Response"), sortable: true },
  { key: "resolution_by", label: __("Resolution"), sortable: true },
  { key: "_assign", label: __("Assigned To"), sortable: false },
];

const contactNames = computed(
  () => customer.doc?.contacts?.map((c) => c.contact_name) ?? []
);

function handleSortClick(column: Column) {
  if (!column.sortable) return;
  if (sort.field === column.key) {
    sort.order = sort.order === "asc" ? "desc" : "asc";
  } else {
    sort.field = column.key;
    sort.order = "desc";
  }
}

const { getStatus } = useTicketStatusStore();

const ticketsListResource: ListResource<HDTicket> = createListResource({
  doctype: "HD Ticket",
  pageLength: 20,
  fields: [
    "name",
    "subject",
    "status",
    "priority",
    "creation",
    "modified",
    "_assign",
    "response_by",
    "resolution_by",
  ],
  filters: {
    customer: customer.doc?.name,
  },
  orderBy: "modified desc",
  transform: (data: HDTicket[]) => {
    return data.map((d) => ({
      ...d,
      statusColor: getStatus(d.status)?.parsed_color || "text-gray-500",
    }));
  },
});

watchDebounced(
  [search, () => sort.field, () => sort.order, () => ({ ...filters })],
  () => {
    ticketsListResource.update({
      filters: {
        customer: customer.doc?.name,
        status: filters.status || undefined,
        priority: filters.priority || undefined,
        contact: filters.contact || undefined,
      },
      orderBy: sort.field ? `${sort.field} ${sort.order}` : undefined,
      orFilters: search.value
        ? {
            subject: ["like", `%${search.value}%`],
            name: ["like", `%${search.value}%`],
          }
        : undefined,
    });
    ticketsListResource.reload();
  },
  { debounce: 300, immediate: true }
);

const filterFields = computed(() => [
  {
    key: "status",
    placeholder: __("Status"),
    doctype: "HD Ticket Status",
    filters: undefined,
  },
  {
    key: "priority",
    placeholder: __("Priority"),
    doctype: "HD Ticket Priority",
    filters: undefined,
  },
  {
    key: "contact",
    placeholder: __("Contact"),
    doctype: "Contact",
    filters: contactNames.value.length
      ? { name: ["in", contactNames.value] }
      : undefined,
  },
]);
</script>
