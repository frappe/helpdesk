<template>
  <div class="flex flex-col">
    <div class="mb-3 flex items-center gap-2">
      <!-- Same search the members list carries. -->
      <TextInput
        v-model="search"
        type="text"
        :placeholder="t('Search')"
        class="min-w-0 flex-1"
      >
        <template #prefix>
          <LucideSearch class="size-4 text-ink-gray-5" />
        </template>
      </TextInput>
    </div>

    <div v-if="tickets.length" class="isolate">
      <div :class="[ROW, 'min-h-8 text-p-xs text-ink-gray-5']">
        <span class="w-14 shrink-0 text-p-sm text-ink-gray-5">{{ t("ID") }}</span>
        <span class="min-w-0 flex-1 overflow-hidden text-ellipsis whitespace-nowrap">{{ t("Subject") }}</span>
        <span class="flex w-36 shrink-0 items-center gap-1.5 text-p-sm text-ink-gray-7">{{ t("Status") }}</span>
        <span class="w-28 shrink-0 text-right text-p-sm text-ink-gray-5">{{ t("Created") }}</span>
      </div>

      <a
        v-for="ticket in tickets"
        :key="ticket.name"
        :class="[ROW, BODY_ROW]"
        :href="`/kb/tickets/${ticket.name}`"
      >
        <span class="w-14 shrink-0 text-p-sm text-ink-gray-5">#{{ ticket.name }}</span>
        <span class="min-w-0 flex-1 overflow-hidden text-ellipsis whitespace-nowrap">{{ ticket.subject }}</span>
        <span class="flex w-36 shrink-0 items-center gap-1.5 text-p-sm text-ink-gray-7">
          <span
            class="size-2 rounded-full"
            :style="{ background: statusMeta(ticket.status).color }"
          />
          {{ statusMeta(ticket.status).label }}
        </span>
        <span class="w-28 shrink-0 text-right text-p-sm text-ink-gray-5">{{
          dayjs(ticket.creation).fromNow()
        }}</span>
      </a>
    </div>

    <p v-if="!loading && !tickets.length" class="py-4 text-p-base text-ink-gray-5">
      {{
        search
          ? t("No tickets match your search.")
          : t("No tickets from this organization yet.")
      }}
    </p>
  </div>
</template>

<script setup lang="ts">
// What this organization has raised lately, beside its people — the settings panel's
// second tab. Ten rows, newest first: enough to answer "is anything open with them at the
// moment", which is the question the panel is being read for. Anything longer belongs in
// the ticket list, which is a click away and made for it.
//
// A plain call rather than `createListResource`: the panel keeps one organization at a
// time, so this is one request per organization opened, and the loading state is the
// thing the empty message has to wait for.
import { ref, watch } from "vue";
import { TextInput, call, dayjs, debounce } from "frappe-ui";
import LucideSearch from "~icons/lucide/search";
import { statusMeta } from "@app/components/ticketCells";
import { t } from "@app/stores/translations";

const ROW =
  "flex items-center gap-3 border-b border-outline-gray-1 last:border-b-0";

// The hover fill is a ::before rather than the row's own background: it reaches past
// the text on both sides without widening the row, and stops a pixel short top and
// bottom so a hovered row still reads as separated from its neighbours instead of
// swallowing the hairlines into one grey band. `isolate` on the table keeps its -z-10
// inside the table rather than letting it slip behind the panel.
const BODY_ROW =
  "relative py-2.5 text-p-base text-ink-gray-8 no-underline before:absolute before:-inset-x-2 before:inset-y-px before:-z-10 before:rounded-md before:content-[''] hover:before:bg-surface-gray-2";

const props = defineProps<{ customer?: string }>();
const RECENT = 10;

const tickets = ref<any[]>([]);
const loading = ref(false);
const search = ref("");

// Searched at the source, not among the ten already on screen: what the reader is looking
// for is usually older than the newest ten, which is the whole reason to type.
async function load() {
  const customer = props.customer;
  if (!customer) {
    tickets.value = [];
    return;
  }
  const filters: Record<string, unknown> = { customer };
  const query = search.value.trim();
  if (query) filters.subject = ["like", `%${query}%`];

  loading.value = true;
  try {
    tickets.value = await call("frappe.client.get_list", {
      doctype: "HD Ticket",
      filters,
      fields: ["name", "subject", "status", "creation"],
      order_by: "creation desc",
      limit_page_length: RECENT,
    });
  } catch {
    tickets.value = [];
  } finally {
    loading.value = false;
  }
}

const searchLater = debounce(load, 300);

watch(
  () => props.customer,
  () => {
    search.value = "";
    load();
  },
  { immediate: true }
);
watch(search, () => searchLater());
</script>
