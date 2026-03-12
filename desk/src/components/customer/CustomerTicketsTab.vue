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
          class="w-48"
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
    <div class="min-h-0 flex flex-1 flex-col">
      <!-- Loading -->
      <template v-if="ticketsListResource.loading">
        <div
          class="py-16 text-center text-sm text-ink-gray-4 flex items-center justify-center"
        >
          <LoadingIndicator :scale="10" />
        </div>
      </template>
      <!-- Empty -->
      <div
        v-else-if="!Boolean(ticketsListResource.data?.length)"
        class="flex flex-col items-center justify-center gap-3 py-16 text-center h-full flex-1"
      >
        <LucideTicket class="h-10 w-10 text-ink-gray-4" />
        <div>
          <!-- make font larger -->
          <p class="text-lg font-medium text-ink-gray-7">
            {{ __("No tickets found.") }}
          </p>
        </div>
      </div>
      <!-- Main Content -->
      <template v-else>
        <!-- Headers -->
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
        <!-- Rows -->
        <div
          class="min-h-0 max-h-[65vh] overflow-y-auto overflow-x-hidden pb-6"
        >
          <div
            v-for="(ticket, i) in ticketsListResource.data"
            :key="ticket.name"
            class="grid items-center px-4 py-3 text-sm text-ink-gray-8 cursor-pointer hover:bg-surface-gray-1 transition-colors"
            :class="i !== ticketRowsCount - 1 && 'border-b border-gray-200'"
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
              <IndicatorIcon :class="getStatus(ticket.status).parsed_color" />
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
          <!-- Load More -->
          <div class="flex justify-center py-6">
            <Button
              v-if="ticketsListResource.hasNextPage"
              :loading="ticketsListResource.loading"
              :label="__('Load More')"
              icon-left="refresh-cw"
              @click="
                () => {
                  ticketsListResource.update({
                    pageLength: ticketsListResource.pageLength + 20,
                  });
                  ticketsListResource.reload();
                }
              "
            />
          </div>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import Link from "@/components/frappe-ui/Link.vue";
import { IndicatorIcon } from "@/components/icons";
import { ticketsListResource } from "@/pages/customer/tickets";
import { useTicketStatusStore } from "@/stores/ticketStatus";
import { __ } from "@/translation";
import { CustomerResourceSymbol } from "@/types";
import { watchDebounced } from "@vueuse/core";
import { dayjsLocal, FormControl, LoadingIndicator } from "frappe-ui";
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

const ticketRowsCount = computed(() => ticketsListResource.data?.length ?? 0);

const { getStatus } = useTicketStatusStore();

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
  { debounce: 300 }
);
</script>
