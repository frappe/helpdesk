<template>
  <section>
    <h2 class="text-md-semibold text-ink-gray-8">{{ __("Docs source") }}</h2>
    <p class="mt-1 text-p-sm text-ink-gray-5">
      {{
        __(
          "Search your docs site from the help center. Nothing is copied into articles."
        )
      }}
    </p>
    <div class="mt-3 flex items-center gap-2">
      <TextInput
        v-model="url"
        class="flex-1"
        placeholder="https://docs.example.com"
        :disabled="connected || busy"
      />
      <template v-if="connected">
        <Button
          v-if="isIndexed"
          :label="syncing ? __('Syncing') : __('Resync')"
          :loading="syncing"
          :disabled="busy"
          @click="resync"
        />
        <Button
          :label="__('Disconnect')"
          :loading="busy"
          @click="disconnect"
        />
      </template>
      <Button
        v-else
        variant="solid"
        :label="__('Connect')"
        :loading="busy"
        :disabled="!url.trim()"
        @click="connect"
      />
    </div>
    <p v-if="error" class="mt-2 text-p-sm text-ink-red-3">{{ error }}</p>
    <p v-else-if="busy && !connected" class="mt-2 text-p-sm text-ink-gray-5">
      {{ __("Reading the docs site. This can take a minute.") }}
    </p>
    <template v-if="connected">
      <p v-if="source?.error" class="mt-2 text-p-sm text-ink-red-3">
        {{ source.error }}
      </p>
      <p v-if="statusLine" class="mt-2 text-p-sm text-ink-gray-5">
        {{ statusLine }}
      </p>
      <p v-if="isIndexed && source?.truncated" class="mt-1 text-p-sm text-ink-amber-3">
        {{ __("Not all pages were indexed.") }}
      </p>
      <div v-if="!isIndexed" class="mt-3">
        <p v-if="source?.sections_error" class="text-p-sm text-ink-gray-5">
          {{ __("The sections could not be read right now.") }}
        </p>
        <div v-else class="space-y-2">
          <Checkbox
            v-for="section in source?.sections"
            :key="section.key"
            :label="section.title"
            :model-value="!section.hidden"
            @update:model-value="(shown) => setShown(section, shown)"
          />
        </div>
      </div>
    </template>
  </section>
</template>

<script setup lang="ts">
import { call, Button, Checkbox, TextInput } from "frappe-ui";
import { computed, onBeforeUnmount, onMounted, ref } from "vue";
import { __ } from "../translation";
import { getErrorMessage, timeAgo } from "../utils";

const API = "helpdesk.api.docs_source";
const POLL_MS = 3000;
const MAX_POLLS = 100;

const url = ref("");
const source = ref<Record<string, any> | null>(null);
const busy = ref(false);
const error = ref("");
let timer: ReturnType<typeof setTimeout> | undefined;

const connected = computed(() => Boolean(source.value));
const isIndexed = computed(
  () => connected.value && source.value?.type !== "Frappe Wiki"
);
const syncing = computed(() => Boolean(source.value?.syncing));
const statusLine = computed(() => {
  const s = source.value;
  if (!s || !isIndexed.value || syncing.value) return "";
  if (!s.synced_on) return __("Not synced yet.");
  return __("{0} pages · synced {1}", [s.page_count, timeAgo(s.synced_on)]);
});

onMounted(async () => {
  source.value = await call(`${API}.get_docs_source`);
  url.value = source.value?.url || "";
  if (isIndexed.value && (syncing.value || !source.value?.synced_on)) {
    poll({ synced_on: null, error: source.value?.error || "" });
  }
});
onBeforeUnmount(() => clearTimeout(timer));

async function connect() {
  await run(async () => {
    source.value = await call(`${API}.connect_docs_source`, { url: url.value });
    // The job is queued after commit, so syncing is false here.
    if (isIndexed.value) poll({ synced_on: null, error: "" });
  });
}

async function resync() {
  const before = { synced_on: source.value?.synced_on, error: source.value?.error };
  await run(async () => {
    await call(`${API}.resync_docs_source`);
    source.value = { ...source.value, syncing: true };
    poll(before);
  });
}

async function disconnect() {
  clearTimeout(timer);
  await run(async () => {
    await call(`${API}.disconnect_docs_source`);
    source.value = null;
    url.value = "";
  });
}

async function setShown(section: Record<string, any>, shown: boolean) {
  const hiddenBefore = section.hidden;
  section.hidden = !shown;
  error.value = "";
  const hidden = source.value!.sections.filter((s) => s.hidden).map((s) => s.key);
  try {
    await call(`${API}.set_hidden_sections`, { sections: hidden });
  } catch (e) {
    section.hidden = hiddenBefore;
    error.value = getErrorMessage(e);
  }
}

// Polls until the sync moves on from `before`; gives up after MAX_POLLS.
function poll(before: { synced_on: unknown; error: string }, count = 0) {
  clearTimeout(timer);
  timer = setTimeout(async () => {
    try {
      source.value = await call(`${API}.get_docs_source`);
    } catch {
      // keep polling through a blip
    }
    const s = source.value;
    const done =
      !s || (!s.syncing && (s.synced_on !== before.synced_on || s.error !== before.error));
    if (!done && count < MAX_POLLS) poll(before, count + 1);
  }, POLL_MS);
}

async function run(action: () => Promise<void>) {
  busy.value = true;
  error.value = "";
  try {
    await action();
  } catch (e) {
    error.value = getErrorMessage(e);
  } finally {
    busy.value = false;
  }
}
</script>
