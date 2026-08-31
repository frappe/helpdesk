<template>
  <div class="kb-org-tickets">
    <div class="kb-org-tickets__toolbar">
      <!-- Inline, not the scoped class: TextInput's root takes no scope id, so a
           scoped rule for it never matches. Same search the members list carries. -->
      <TextInput
        v-model="search"
        type="text"
        :placeholder="t('Search')"
        :style="{ flex: 1, minWidth: 0 }"
      >
        <template #prefix>
          <LucideSearch class="size-4 text-ink-gray-5" />
        </template>
      </TextInput>
    </div>

    <div v-if="tickets.length" class="kb-org-tickets__table">
      <div class="kb-org-tickets__row kb-org-tickets__head">
        <span class="kb-org-tickets__id">{{ t("ID") }}</span>
        <span class="kb-org-tickets__subject">{{ t("Subject") }}</span>
        <span class="kb-org-tickets__status">{{ t("Status") }}</span>
        <span class="kb-org-tickets__age">{{ t("Created") }}</span>
      </div>

      <a
        v-for="ticket in tickets"
        :key="ticket.name"
        class="kb-org-tickets__row kb-org-tickets__body-row"
        :href="`/kb/tickets/${ticket.name}`"
      >
        <span class="kb-org-tickets__id">#{{ ticket.name }}</span>
        <span class="kb-org-tickets__subject">{{ ticket.subject }}</span>
        <span class="kb-org-tickets__status">
          <span
            class="kb-org-tickets__dot"
            :style="{ background: statusMeta(ticket.status).color }"
          />
          {{ statusMeta(ticket.status).label }}
        </span>
        <span class="kb-org-tickets__age">{{
          dayjs(ticket.creation).fromNow()
        }}</span>
      </a>
    </div>

    <p v-if="!loading && !tickets.length" class="kb-org-tickets__empty">
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

<style scoped>
.kb-org-tickets {
  display: flex;
  flex-direction: column;
}

.kb-org-tickets__toolbar {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
}

.kb-org-tickets__row {
  display: flex;
  font-size: 14px;
  align-items: center;
  gap: 12px;
  padding: 10px 0;
  border-bottom: 1px solid var(--outline-gray-1);
  color: var(--ink-gray-8);
  text-decoration: none;
}

.kb-org-tickets__row:last-child {
  border-bottom: 0;
}

/* The fill is a pseudo rather than the row's own background. It can then reach past the
   text on both sides without widening the row — and stop a pixel short top and bottom, so
   a hovered row still reads as separated from the ones around it instead of swallowing
   the hairlines into one grey band. */
.kb-org-tickets__body-row {
  position: relative;
}

.kb-org-tickets__body-row::before {
  content: "";
  position: absolute;
  inset: 1px -8px;
  z-index: -1;
  border-radius: 6px;
}

.kb-org-tickets__body-row:hover::before {
  background: var(--surface-gray-2);
}

/* Keeps the hover fill's `z-index: -1` inside the table rather than letting it slip
   behind the panel. */
.kb-org-tickets__table {
  isolation: isolate;
}

/* The column names, in the same quiet type the members table sets them in. */
.kb-org-tickets__head {
  min-height: 32px;
  padding: 0;
  font-size: 12px;
  line-height: 16px;
  color: var(--ink-gray-5);
}

.kb-org-tickets__id {
  flex-shrink: 0;
  width: 56px;
  color: var(--ink-gray-5);
  font-size: 13px;
}

.kb-org-tickets__subject {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.kb-org-tickets__status {
  display: flex;
  flex-shrink: 0;
  align-items: center;
  gap: 6px;
  width: 9rem;
  font-size: 13px;
  color: var(--ink-gray-7);
}

.kb-org-tickets__dot {
  width: 8px;
  height: 8px;
  border-radius: 9999px;
}

.kb-org-tickets__age {
  flex-shrink: 0;
  width: 7rem;
  text-align: right;
  font-size: 13px;
  color: var(--ink-gray-5);
}

.kb-org-tickets__empty {
  padding: 16px 0;
  font-size: 14px;
  color: var(--ink-gray-5);
}
</style>
