<template>
  <div class="flex min-h-0 flex-col">
    <div class="mb-3 flex shrink-0 items-center gap-2">
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

    <template v-if="tickets.data?.length || isFirstLoad">
      <div :class="[ROW, 'min-h-8 shrink-0 text-p-xs text-ink-gray-5']">
        <span class="w-14 shrink-0">{{ __("ID") }}</span>
        <span class="min-w-0 flex-1 truncate">{{ __("Subject") }}</span>
        <span class="w-36 shrink-0 max-sm:w-auto">{{ __("Status") }}</span>
        <span class="w-28 shrink-0 text-right max-sm:hidden">{{
          __("Created")
        }}</span>
      </div>

      <div
        v-if="isFirstLoad"
        class="min-h-0 flex-1 overflow-hidden"
        aria-busy="true"
      >
        <span class="sr-only" role="status">{{ __("Loading") }}</span>
        <div v-for="i in 8" :key="i" :class="[ROW, 'py-2.5']">
          <span class="flex h-[21px] w-14 shrink-0 items-center">
            <Skeleton :class="[BLOCK, 'h-2 w-9 rounded-full']" />
          </span>
          <span class="flex min-w-0 flex-1 items-center">
            <Skeleton
              :class="[BLOCK, 'h-2.5 rounded-full']"
              :style="{ width: `${40 + ((i * 23) % 40)}%` }"
            />
          </span>
          <span class="flex w-36 shrink-0 items-center gap-1.5 max-sm:w-auto">
            <Skeleton :class="[BLOCK, 'size-2 rounded-full']" />
            <Skeleton :class="[BLOCK, 'h-2 w-16 rounded-full']" />
          </span>
          <span class="flex w-28 shrink-0 justify-end max-sm:hidden">
            <Skeleton :class="[BLOCK, 'h-2 w-16 rounded-full']" />
          </span>
        </div>
      </div>
      <!-- -mx-2/px-2: room for the rows' 8px hover bleed. -->
      <div
        v-else
        class="portal-reveal isolate -mx-2 min-h-0 flex-1 overflow-y-auto px-2"
      >
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
        <!-- A full last page shows Load More once, then it hides. -->
        <div v-if="tickets.hasNextPage" class="mt-3 flex justify-center">
          <Button
            :label="__('Load More')"
            icon-left="lucide-refresh-cw"
            :loading="tickets.list.loading"
            @click="tickets.next()"
          />
        </div>
      </div>
    </template>

    <p
      v-if="
        tickets.list.fetched && !tickets.list.loading && !tickets.data?.length
      "
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
import { computed, ref, watch } from "vue";
import { RouterLink } from "vue-router";
import {
  Button,
  Skeleton,
  TextInput,
  createListResource,
  debounce,
} from "frappe-ui";
import LucideSearch from "~icons/lucide/search";
import { __ } from "@helpdesk/shared/translation";
import { SEARCH_DEBOUNCE_MS, timeAgo } from "@helpdesk/shared/utils";
import PortalStatusPill from "@app/components/ticket/PortalStatusPill.vue";
import { ROUTES } from "@helpdesk/shared/portalRoutes";
import { loadStatuses, statusMeta } from "@app/stores/ticketMeta";

const PAGE_LENGTH = 20;

const ROW =
  "flex items-center gap-3 border-b border-outline-gray-1 px-0.5 last:border-b-0";

const BODY_ROW =
  "relative py-2.5 text-p-base text-ink-gray-8 no-underline before:absolute before:-inset-x-2 before:inset-y-px before:-z-10 before:rounded-5 before:content-[''] hover:before:bg-surface-gray-2";

const props = defineProps<{ customer?: string }>();

// Settings may open before any page loaded status colours.
loadStatuses();

const tickets = createListResource({
  doctype: "HD Ticket",
  fields: ["name", "subject", "status", "creation"],
  orderBy: "creation desc",
  pageLength: PAGE_LENGTH,
});
const search = ref("");

// First page only: a new search keeps old rows until its own arrive.
const isFirstLoad = computed(
  () => !tickets.list.fetched && !tickets.data?.length
);
const BLOCK = "motion-reduce:animate-none";

function load() {
  if (!props.customer) return;
  // IDs show as "#123".
  const query = search.value.trim().replace(/^#/, "");
  const like = ["like", `%${query}%`];
  tickets.update({
    filters: { customer: props.customer },
    orFilters: query ? { name: like, subject: like, status: like } : null,
    start: 0,
  });
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
