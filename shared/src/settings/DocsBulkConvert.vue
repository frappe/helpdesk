<template>
  <div class="mt-6">
    <h3 class="text-base-medium text-ink-gray-8">
      {{ __("Convert to articles") }}
    </h3>
    <p class="mt-1 text-p-sm text-ink-gray-5">
      {{
        __("Copy docs pages into draft articles, up to {0} at a time.", [MAX])
      }}
    </p>
    <TextInput
      v-model="query"
      class="mt-2"
      :placeholder="__('Search pages')"
      :aria-label="__('Search pages')"
    />
    <p v-if="error" class="mt-2 text-p-sm text-ink-red-3">{{ error }}</p>
    <p v-if="searching" class="mt-2 text-p-sm text-ink-gray-5">
      {{ __("Loading all sections") }}
    </p>
    <div v-for="group in groups" :key="group.key" class="mt-2">
      <button
        type="button"
        class="flex w-full items-center gap-1 text-base-medium text-ink-gray-7"
        :aria-expanded="isOpen(group.key)"
        @click="toggle(group.key)"
      >
        <span
          :class="
            isOpen(group.key) ? 'lucide-chevron-down' : 'lucide-chevron-right'
          "
          class="size-4"
        />
        {{ group.title }}
      </button>
      <div v-if="isOpen(group.key)" class="ms-5 mt-1 space-y-1.5">
        <p v-if="loading[group.key]" class="text-p-sm text-ink-gray-5">
          {{ __("Loading") }}
        </p>
        <div v-for="p in visible(group.key)" :key="p.route">
          <a
            v-if="p.converted"
            :href="articleHref(p.converted.name)"
            target="_blank"
            rel="noopener"
            class="text-p-sm text-ink-gray-6 underline"
            >{{ p.converted.title }}</a
          >
          <template v-else>
            <Checkbox
              :label="p.title"
              :model-value="picked.has(p.route)"
              :disabled="!picked.has(p.route) && full"
              @update:model-value="(on) => tick(p.route, on)"
            />
            <a
              v-if="p.matching"
              :href="articleHref(p.matching.name)"
              target="_blank"
              rel="noopener"
              class="ms-6 text-p-sm text-ink-amber-6 underline"
              >{{ __("Matching article: {0}", [p.matching.title]) }}</a
            >
          </template>
        </div>
      </div>
    </div>
    <p v-if="full" class="mt-2 text-p-sm text-ink-gray-5">
      {{ __("You can pick up to {0} pages at a time.", [MAX]) }}
    </p>
    <div class="mt-3 flex items-center gap-3">
      <Button
        :label="pagesLabel(picked.size)"
        :disabled="!picked.size || running"
        :loading="running"
        @click="showDialog = true"
      />
      <p v-if="result && !running" class="text-p-sm text-ink-gray-6">
        {{ __("{0} created, {1} skipped", [result.created, result.skipped]) }}
      </p>
    </div>
    <DocsConvertDialog
      v-model:open="showDialog"
      bulk
      :routes="[...picked]"
      @done="onEnqueued"
    />
  </div>
</template>

<script setup lang="ts">
import { Button, Checkbox, TextInput } from "frappe-ui";
import {
  computed,
  onBeforeUnmount,
  onMounted,
  reactive,
  ref,
  watch,
} from "vue";
import { __ } from "../translation";
import { getErrorMessage } from "../utils";
import DocsConvertDialog from "./DocsConvertDialog.vue";
import { getDocs } from "./docsApi";
import { articleHref, pagesLabel } from "./docsLinks";

const MAX = 50;
const POLL_MS = 2000;
const POLL_CAP_MS = 5 * 60_000;
const MAX_POLL_FAILURES = 5;

const props = defineProps<{ source: Record<string, any> }>();

const query = ref("");
const error = ref("");
const showDialog = ref(false);
const running = ref(false);
const searching = ref(false);
const result = ref<{ created: number; skipped: number } | null>(null);
const picked = ref(new Set<string>());
const pages = reactive<Record<string, any[]>>({});
const loading = reactive<Record<string, boolean>>({});
const opened = reactive<Record<string, boolean>>({});
let timer: ReturnType<typeof setTimeout> | undefined;
let unmounted = false;
let searched = false;

const isWiki = computed(() => props.source.type === "Frappe Wiki");
const full = computed(() => picked.value.size >= MAX);
const sections = computed(() =>
  (props.source.sections || []).filter((s) => !s.hidden)
);
const groups = computed(() =>
  isWiki.value
    ? sections.value.map((s) => ({ key: s.key, title: s.title }))
    : Object.keys(pages).map((key) => ({ key, title: key }))
);

onMounted(async () => {
  // Wiki sections load when opened; an indexed site loads once.
  if (!isWiki.value) load(null);
  try {
    const cached = await getDocs("get_bulk_convert_result");
    if (!unmounted && !result.value) result.value = cached;
  } catch {
    // no cached report is fine
  }
});
onBeforeUnmount(() => {
  unmounted = true;
  clearTimeout(timer);
});

// The first search needs every section, so load the unopened ones in turn.
watch(query, async (q) => {
  if (!isWiki.value || !q.trim() || searched) return;
  searched = true;
  searching.value = true;
  for (const { key } of sections.value) {
    if (unmounted) return;
    if (!pages[key]) await load(key);
  }
  searching.value = false;
});

const isOpen = (key: string) => opened[key] || Boolean(query.value.trim());

function visible(key: string) {
  const q = query.value.trim().toLowerCase();
  return (pages[key] || []).filter((p) => p.title.toLowerCase().includes(q));
}

function toggle(key: string) {
  opened[key] = !opened[key];
  if (opened[key] && isWiki.value && !pages[key]) load(key);
}

async function load(section: string | null) {
  const key = section || "";
  loading[key] = true;
  error.value = "";
  try {
    const rows = await getDocs("list_docs_pages", section ? { section } : {});
    if (unmounted) return;
    if (section) return (pages[section] = rows);
    for (const row of rows) (pages[row.section] ||= []).push(row);
  } catch (e) {
    if (!unmounted) error.value = getErrorMessage(e);
  } finally {
    loading[key] = false;
  }
}

function reload() {
  const keys = Object.keys(pages);
  keys.forEach((key) => delete pages[key]);
  if (!isWiki.value) return load(null);
  keys.forEach((key) => load(key));
}

function tick(route: string, on: boolean) {
  const next = new Set(picked.value);
  on ? next.add(route) : next.delete(route);
  picked.value = next;
}

function onEnqueued() {
  running.value = true;
  result.value = null;
  picked.value = new Set();
  poll(Date.now(), 0);
}

function poll(started: number, failures: number) {
  timer = setTimeout(async () => {
    let failed = failures;
    try {
      const done = await getDocs("get_bulk_convert_result");
      if (unmounted) return;
      failed = 0;
      if (done) {
        result.value = done;
        running.value = false;
        return reload();
      }
    } catch (e) {
      if (unmounted) return;
      if (++failed >= MAX_POLL_FAILURES) return stop(getErrorMessage(e));
    }
    if (Date.now() - started > POLL_CAP_MS) {
      return stop(__("The bulk convert is taking too long. Check back later."));
    }
    poll(started, failed);
  }, POLL_MS);
}

function stop(message: string) {
  running.value = false;
  error.value = message;
}
</script>
