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
        style="grid-template-columns: 6rem 1fr 9rem 8rem 7rem 7rem 9rem"
      >
        <div
          v-for="col in columns"
          :key="col.key"
          class="group flex items-center gap-1 select-none text-ink-gray-5"
          :class="col.sortable ? 'hover:text-ink-gray-8' : ''"
          @click="handleSortClick(col.key)"
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
            @click="
              () => {
                if (sort.field === col.key) {
                  sort.order = sort.order === 'asc' ? 'desc' : 'asc';
                } else {
                  sort.field = col.key;
                  sort.order = 'asc';
                }
              }
            "
          />
        </div>
      </div>

      <!-- Rows -->
      <div
        v-for="(ticket, i) in filteredTickets"
        :key="ticket.name"
        class="grid items-center px-4 py-3 text-sm text-ink-gray-8 cursor-pointer hover:bg-surface-gray-1 transition-colors"
        :class="i !== filteredTickets.length - 1 && 'border-b border-gray-200'"
        style="grid-template-columns: 6rem 1fr 9rem 8rem 7rem 7rem 9rem"
      >
        <!-- ID -->
        <div class="text-ink-gray-6 font-base">{{ ticket.name }}</div>

        <!-- Subject -->
        <div class="truncate font-medium">{{ ticket.subject }}</div>

        <!-- Status -->
        <div class="flex items-center gap-1.5">
          <IndicatorIcon :class="ticket.statusColor" />
          <span>{{ ticket.status }}</span>
        </div>

        <!-- Priority -->
        <div class="flex items-center gap-1.5">
          <span
            class="inline-block h-2 w-2 rounded-full"
            :class="ticket.priorityColor"
          />
          <span>{{ ticket.priority }}</span>
        </div>

        <!-- Created -->
        <div class="text-ink-gray-5">{{ ticket.created }}</div>

        <!-- Last Updated -->
        <div class="text-ink-gray-5">{{ ticket.modified }}</div>

        <!-- Assigned To -->
        <div class="flex items-center gap-2">
          <Avatar
            size="xs"
            :label="ticket.assignedTo"
            :image="ticket.assignedImage"
          />
          <span class="truncate">{{ ticket.assignedTo }}</span>
        </div>
      </div>

      <!-- Empty -->
      <div
        v-if="!filteredTickets.length"
        class="py-16 text-center text-sm text-ink-gray-4"
      >
        {{ __("No tickets found.") }}
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { IndicatorIcon } from "@/components/icons";
import { __ } from "@/translation";
import { CustomerResourceSymbol } from "@/types";
import { Avatar, FormControl } from "frappe-ui";
import { Link } from "frappe-ui/frappe";
import { computed, inject, reactive, ref } from "vue";
import LucideSearch from "~icons/lucide/search";

const customer = inject(CustomerResourceSymbol)!;

const search = ref("");
const sort = reactive<{ field: string | null; order: "asc" | "desc" }>({
  field: null,
  order: "asc",
});

const columns = [
  { key: "name", label: __("Ticket ID"), sortable: true },
  { key: "subject", label: __("Subject"), sortable: true },
  { key: "status", label: __("Status"), sortable: true },
  { key: "priority", label: __("Priority"), sortable: true },
  { key: "created", label: __("Created"), sortable: true },
  { key: "modified", label: __("Last Updated"), sortable: true },
  { key: "assignedTo", label: __("Assigned To"), sortable: false },
];

const contactNames = computed(
  () => customer.doc?.contacts?.map((c) => c.contact_name) ?? []
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

const filters = reactive<Record<string, string>>({
  status: "",
  priority: "",
  contact: "",
});

// --- Dummy data ---
interface TicketRow {
  name: string;
  subject: string;
  status: string;
  statusColor: string;
  priority: string;
  priorityColor: string;
  created: string;
  modified: string;
  assignedTo: string;
  assignedImage: string;
  contact: string;
}

const tickets: TicketRow[] = [
  {
    name: "#14231",
    subject: "Login issue on portal",
    status: "Open",
    statusColor: "text-gray-500",
    priority: "High",
    priorityColor: "bg-red-500",
    created: "Oct 22",
    modified: "45m ago",
    assignedTo: "Jamie",
    assignedImage: "",
    contact: "Jamie",
  },
  {
    name: "#14231",
    subject: "Payment failed repeatedly",
    status: "Replied",
    statusColor: "text-blue-500",
    priority: "Medium",
    priorityColor: "bg-gray-400",
    created: "Sep 15",
    modified: "45m ago",
    assignedTo: "Alex Bright",
    assignedImage: "",
    contact: "Alex Bright",
  },
  {
    name: "#14233",
    subject: "Account locked due to suspicious activity",
    status: "Open",
    statusColor: "text-gray-500",
    priority: "Low",
    priorityColor: "bg-gray-400",
    created: "Oct 21",
    modified: "1h ago",
    assignedTo: "Jordan",
    assignedImage: "",
    contact: "Jordan",
  },
  {
    name: "#14233",
    subject: "Feature request for dark mode",
    status: "Open",
    statusColor: "text-gray-500",
    priority: "Low",
    priorityColor: "bg-gray-400",
    created: "Oct 20",
    modified: "2h ago",
    assignedTo: "Sam",
    assignedImage: "",
    contact: "Sam",
  },
  {
    name: "#14235",
    subject: "Unable to reset password",
    status: "Open",
    statusColor: "text-gray-500",
    priority: "High",
    priorityColor: "bg-red-500",
    created: "Oct 19",
    modified: "3h ago",
    assignedTo: "Taylor",
    assignedImage: "",
    contact: "Taylor",
  },
  {
    name: "#14236",
    subject: "Website downtime reported",
    status: "Replied",
    statusColor: "text-blue-500",
    priority: "Medium",
    priorityColor: "bg-gray-400",
    created: "Oct 18",
    modified: "4h ago",
    assignedTo: "Morgan Fields",
    assignedImage: "",
    contact: "Morgan Fields",
  },
  {
    name: "#14237",
    subject: "API integration issues",
    status: "Replied",
    statusColor: "text-blue-500",
    priority: "Medium",
    priorityColor: "bg-gray-400",
    created: "Oct 17",
    modified: "5h ago",
    assignedTo: "Jamie Spark",
    assignedImage: "",
    contact: "Jamie Spark",
  },
  {
    name: "#14237",
    subject: "User feedback on UI design",
    status: "Open",
    statusColor: "text-gray-500",
    priority: "Low",
    priorityColor: "bg-gray-400",
    created: "Oct 16",
    modified: "5h ago",
    assignedTo: "Casey Lane",
    assignedImage: "",
    contact: "Casey Lane",
  },
  {
    name: "#14239",
    subject: "Security patch update needed",
    status: "Open",
    statusColor: "text-gray-500",
    priority: "High",
    priorityColor: "bg-red-500",
    created: "Oct 15",
    modified: "7h ago",
    assignedTo: "Riley Stone",
    assignedImage: "",
    contact: "Riley Stone",
  },
];

const filteredTickets = computed(() => {
  const result = tickets.filter((t) => {
    const q = search.value.toLowerCase();
    const matchSearch =
      !q ||
      t.subject.toLowerCase().includes(q) ||
      t.name.toLowerCase().includes(q);
    const matchStatus = !filters.status || t.status === filters.status;
    const matchPriority = !filters.priority || t.priority === filters.priority;
    const matchContact = !filters.contact || t.contact === filters.contact;
    return matchSearch && matchStatus && matchPriority && matchContact;
  });

  return result;
});

function handleSortClick(column: string) {
  if (sort.field === column) {
    sort.order = sort.order === "asc" ? "desc" : "asc";
  } else {
    sort.field = column;
    sort.order = "asc";
  }
}
</script>
