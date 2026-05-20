<template>
  <div class="flex h-full w-full flex-col overflow-auto p-5 px-10 pb-10">
    <LayoutHeader>
      <template #left-header>
        <Breadcrumbs
          :items="[
            { label: 'My Tickets', route: { name: 'TicketsCustomer' } },
            { label: 'Find Answers', route: { name: 'CustomerSearch' } },
          ]"
          class="-ml-[2px]"
        />
      </template>
    </LayoutHeader>

    <div class="mx-auto w-full max-w-2xl pt-8 flex flex-col gap-6">
      <div class="flex flex-col gap-2">
        <h1 class="text-2xl font-semibold text-ink-gray-9">
          How can we help you?
        </h1>
        <p class="text-p-sm text-ink-gray-6">
          Describe your issue and we'll find relevant articles before you submit
          a ticket.
        </p>
      </div>

      <div class="flex flex-col">
        <div class="flex gap-2 items-center">
          <TextInput
            ref="inputRef"
            v-model="query"
            class="flex-1"
            placeholder="e.g. How do I reset my password?"
            size="md"
            @keydown.enter="handleSearch"
          />
          <Button
            variant="solid"
            size="md"
            :disabled="!canSearch"
            @click="handleSearch"
          >
            <LucideArrowRight class="size-4" />
          </Button>
        </div>
        <p class="text-p-xs text-ink-gray-5 pl-1 mt-1 h-4">
          <span v-if="query.length > 0 && query.length < MIN_QUERY_LENGTH">
            Please enter at least {{ MIN_QUERY_LENGTH }} characters
          </span>
        </p>
      </div>

      <div v-if="loading" class="flex flex-col gap-4">
        <div
          v-for="i in 3"
          :key="i"
          class="h-4 rounded-lg bg-surface-gray-2 animate-pulse"
        />
      </div>

      <div
        v-else-if="error"
        class="rounded-lg border border-outline-gray-2 bg-surface-gray-1 p-4 text-p-sm text-ink-gray-7"
      >
        Something went wrong while searching. Please try again.
      </div>

      <template v-else-if="searched">
        <div
          v-if="answer"
          class="rounded-lg border border-outline-gray-2 bg-surface-white"
        >
          <Section :opened="answerOpen" :collapsible="true" :hide-label="true">
            <template #header="{ opened, toggle }">
              <div
                class="flex items-center justify-between cursor-pointer select-none p-4"
                @click="toggle"
              >
                <div class="flex items-center gap-2">
                  <LucideSparkles class="size-4 text-ink-gray-7 shrink-0" />
                  <span class="text-sm font-medium text-ink-gray-8">
                    AI Answer
                  </span>
                </div>
                <LucideChevronDown
                  class="size-4 text-ink-gray-5 transition-transform duration-200"
                  :class="{ 'rotate-180': opened }"
                />
              </div>
            </template>
            <TextEditor
              :content="answer"
              :editable="false"
              editor-class="prose prose-sm max-w-none text-ink-gray-7 leading-relaxed px-4 pb-4"
            />
          </Section>
        </div>

        <div v-if="articles.length" class="flex flex-col gap-2">
          <p class="text-sm font-medium text-ink-gray-7">Related articles</p>
          <RouterLink
            v-for="article in articles"
            :key="article.name"
            :to="{ name: 'ArticlePublic', params: { articleId: article.name } }"
            class="flex items-center justify-between rounded-lg border border-outline-gray-2 bg-surface-white px-4 py-3 hover:bg-surface-gray-1 transition-colors group"
          >
            <span class="text-p-sm text-ink-gray-8 group-hover:text-ink-gray-9">
              {{ article.title }}
            </span>
            <LucideArrowRight
              class="size-4 text-ink-gray-4 group-hover:text-ink-gray-6 shrink-0"
            />
          </RouterLink>
        </div>

        <div
          v-else-if="!answer"
          class="text-p-sm text-ink-gray-6 text-center py-4"
        >
          No articles found for your query.
        </div>

        <div
          class="rounded-lg border border-outline-gray-2 bg-surface-gray-1 px-4 py-3 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between"
        >
          <div class="flex flex-col gap-1">
            <p class="text-sm font-medium text-ink-gray-8">Still need help?</p>
            <p class="text-p-sm text-ink-gray-6">
              If these articles didn't answer your question, submit a support
              ticket and our team will get back to you.
            </p>
          </div>
          <Button
            label="Submit a ticket"
            theme="gray"
            variant="solid"
            class="shrink-0"
            @click="router.push({ name: 'TicketNew' })"
          />
        </div>
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import { LayoutHeader } from "@/components";
import Section from "@/components/Section.vue";
import {
  Breadcrumbs,
  Button,
  createResource,
  TextEditor,
  TextInput,
} from "frappe-ui";
import { computed, onMounted, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import LucideArrowRight from "~icons/lucide/arrow-right";
import LucideChevronDown from "~icons/lucide/chevron-down";
import LucideSparkles from "~icons/lucide/sparkles";

const STORAGE_KEY_PREFIX = "helpdesk_customer_search:";
const MIN_QUERY_LENGTH = 10;

const router = useRouter();
const route = useRoute();

const inputRef = ref<InstanceType<typeof TextInput> | null>(null);
const query = ref("");
const loading = ref(false);
const error = ref(false);
const searched = ref(false);
const answer = ref("");
const articles = ref<{ name: string; title: string; score: number }[]>([]);
const answerOpen = ref(true);
const lastSearchedQuery = ref("");

const canSearch = computed(
  () =>
    query.value.trim().length >= MIN_QUERY_LENGTH &&
    !loading.value &&
    !(searched.value && query.value.trim() === lastSearchedQuery.value)
);

const searchResource = createResource({
  url: "helpdesk.rag.rag_search.rag_search",
  onSuccess(data: { answer: string; articles: typeof articles.value }) {
    answer.value = data.answer || "";
    articles.value = data.articles || [];
    loading.value = false;
    searched.value = true;
    error.value = false;
    lastSearchedQuery.value = query.value.trim();
    saveToCache(query.value, data);
  },
  onError() {
    loading.value = false;
    error.value = true;
    searched.value = true;
  },
});

function handleSearch() {
  if (!canSearch.value) return;
  const q = query.value.trim();
  lastSearchedQuery.value = q;
  loading.value = true;
  error.value = false;
  searched.value = false;
  answer.value = "";
  articles.value = [];
  answerOpen.value = true;
  router.replace({ name: "CustomerSearch", query: { q } });
  searchResource.submit({ query: q });
}

function cacheKey(q: string) {
  return `${STORAGE_KEY_PREFIX}${q}`;
}

function saveToCache(
  q: string,
  data: { answer: string; articles: typeof articles.value }
) {
  localStorage.setItem(
    cacheKey(q),
    JSON.stringify({ data, timestamp: Date.now() })
  );
}

function loadFromCache(q: string): boolean {
  const raw = localStorage.getItem(cacheKey(q));
  if (!raw) return false;
  try {
    const { data, timestamp } = JSON.parse(raw);
    if (Date.now() - timestamp > 30 * 60 * 1000) {
      localStorage.removeItem(cacheKey(q));
      return false;
    }
    answer.value = data.answer || "";
    articles.value = data.articles || [];
    searched.value = true;
    lastSearchedQuery.value = q;
    return true;
  } catch {
    return false;
  }
}

watch(query, (val) => {
  if (val !== route.query.q) {
    router.replace({ name: "CustomerSearch", query: val ? { q: val } : {} });
  }
});

watch(
  () => route.query.q,
  (newQ) => {
    if (newQ && typeof newQ === "string" && newQ !== query.value) {
      query.value = newQ;
      if (!loadFromCache(newQ)) {
        loading.value = true;
        error.value = false;
        searched.value = false;
        answer.value = "";
        articles.value = [];
        searchResource.submit({ query: newQ });
      }
    } else if (!newQ && query.value) {
      query.value = "";
      answer.value = "";
      articles.value = [];
      searched.value = false;
    }
  }
);

onMounted(() => {
  const q = route.query.q as string | undefined;
  if (q) {
    query.value = q;
    if (!loadFromCache(q)) {
      loading.value = true;
      searchResource.submit({ query: q });
    }
  }
  inputRef.value?.$el?.querySelector("input")?.focus();
});
</script>
