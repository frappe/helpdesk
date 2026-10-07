<template>
  <div class="flex flex-col">
    <div class="mb-3 flex items-center gap-2">
      <TextInput
        v-model="search"
        type="text"
        :placeholder="__('Search')"
        class="min-w-0 flex-1"
      >
        <template #prefix>
          <LucideSearch class="size-4 text-ink-gray-5" />
        </template>
      </TextInput>
    </div>

    <div v-if="tickets.data?.length" class="isolate">
      <div :class="[ROW, 'min-h-8 text-p-xs text-ink-gray-5']">
        <span class="w-14 shrink-0 text-p-sm text-ink-gray-5">{{
          __("ID")
        }}</span>
        <span class="min-w-0 flex-1 truncate">{{ __("Subject") }}</span>
        <span class="w-36 shrink-0 text-p-sm text-ink-gray-7 max-sm:w-auto">{{
          __("Status")
        }}</span>
        <span
          class="w-28 shrink-0 text-right text-p-sm text-ink-gray-5 max-sm:hidden"
          >{{ __("Created") }}</span
        >
      </div>

      <RouterLink
        v-for="ticket in tickets.data"
        :key="ticket.name"
        :class="[ROW, BODY_ROW]"
        :to="ROUTES.ticket(ticket.name)"
      >
        <span class="w-14 shrink-0 text-p-sm text-ink-gray-5"
          >#{{ ticket.name }}</span
        >
        <span class="min-w-0 flex-1 truncate">{{ ticket.subject }}</span>
        <PortalStatusPill
          class="w-36 shrink-0 max-sm:w-auto"
          v-bind="statusMeta(ticket.status)"
        />
        <span
          class="w-28 shrink-0 text-right text-p-sm text-ink-gray-5 max-sm:hidden"
          >{{ timeAgo(ticket.creation) }}</span
        >
      </RouterLink>
    </div>

    <p
      v-if="!tickets.loading && !tickets.data?.length"
      class="py-4 text-p-base text-ink-gray-5"
    >
      {{
        search
          ? __("No tickets match your search.")
          : __("No tickets from this organization yet.")
      }}
    </p>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from "vue";
import { RouterLink } from "vue-router";
import { TextInput, createListResource, debounce } from "frappe-ui";
import LucideSearch from "~icons/lucide/search";
import { __ } from "@helpdesk/shared/translation";
import { timeAgo } from "@helpdesk/shared/utils";
import PortalStatusPill from "@app/components/ticket/PortalStatusPill.vue";
import { ROUTES } from "@app/routes";
import { statusMeta } from "@app/stores/ticketMeta";
import { SEARCH_DEBOUNCE_MS } from "@app/utils";

const RECENT_TICKET_LIMIT = 10;

const ROW =
  "flex items-center gap-3 border-b border-outline-gray-1 last:border-b-0";

const BODY_ROW =
  "relative py-2.5 text-p-base text-ink-gray-8 no-underline before:absolute before:-inset-x-2 before:inset-y-px before:-z-10 before:rounded-5 before:content-[''] hover:before:bg-surface-gray-2";

const props = defineProps<{ customer?: string }>();

const tickets = createListResource({
  doctype: "HD Ticket",
  fields: ["name", "subject", "status", "creation"],
  orderBy: "creation desc",
  pageLength: RECENT_TICKET_LIMIT,
});
const search = ref("");

function load() {
  if (!props.customer) return;
  const filters: Record<string, unknown> = { customer: props.customer };
  const query = search.value.trim();
  if (query) filters.subject = ["like", `%${query}%`];
  tickets.update({ filters });
  tickets.reload();
}

watch(
  () => props.customer,
  () => {
    search.value = "";
    load();
  },
  { immediate: true }
);
watch(search, debounce(load, SEARCH_DEBOUNCE_MS));
</script>
