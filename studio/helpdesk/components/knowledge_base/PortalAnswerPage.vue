<template>
  <div
    class="mx-auto flex w-full max-w-[700px] flex-1 flex-col gap-6 px-4 pb-10 pt-6 md:px-0 sm:pt-[41px]"
  >
    <div class="flex flex-col gap-4">
      <PortalLink
        :to="ROUTES.home"
        class="flex w-fit items-center gap-1.5 text-p-sm text-ink-gray-5 hover:text-ink-gray-8"
      >
        <LucideArrowLeft class="size-4" />
        {{ __("Help center") }}
      </PortalLink>
      <PortalArticleSearch
        :initial-query="question"
        :placeholder="__('Ask a question or search articles')"
      />
    </div>

    <Transition name="answer" mode="out-in" appear>
      <section
        v-if="isLoading"
        key="loading"
        class="flex flex-col gap-4"
        role="status"
        aria-live="polite"
      >
        <h1 class="break-words text-xl font-semibold text-ink-gray-9">
          {{ question }}
        </h1>
        <p class="flex items-center gap-2 text-p-sm text-ink-gray-5">
          <LucideSparkles class="thinking size-4 text-ink-gray-6" />
          {{ __("Reading the knowledge base…") }}
        </p>
        <div class="flex flex-col gap-2.5" aria-hidden="true">
          <div
            v-for="width in SKELETON_WIDTHS"
            :key="width"
            class="thinking h-3.5 rounded-full bg-surface-gray-2"
            :style="{ width }"
          />
        </div>
      </section>

      <section
        v-else-if="showMatches"
        key="matches"
        class="flex flex-col gap-4"
      >
        <h1 class="break-words text-xl font-semibold text-ink-gray-9">
          {{ question }}
        </h1>
        <p v-if="isFailed" class="text-p-base text-ink-gray-6">
          {{
            matches.data?.length
              ? __(
                  "We couldn't write an answer just now. These articles may help."
                )
              : __(
                  "We couldn't write an answer just now. Please try again later."
                )
          }}
        </p>
        <PortalArticleList
          v-if="matches.data?.length"
          :articles="matches.data"
        />
        <PortalEmptyState
          v-else-if="matches.settledQuery && !isFailed"
          :title="__('No articles found')"
          :description="__('Try other words, or ask our team.')"
        />
      </section>

      <section
        v-else-if="answer.data"
        :key="`answer-${question}`"
        class="flex flex-col gap-8"
      >
        <div class="flex flex-col gap-4">
          <h1 class="break-words text-xl font-semibold text-ink-gray-9">
            {{ question }}
          </h1>
          <div
            v-if="answer.data.answer"
            class="flex items-center gap-1.5 text-p-sm font-medium text-ink-gray-6"
          >
            <LucideSparkles class="size-4" />
            {{ __("Answer") }}
          </div>
          <p v-if="answer.data.refused" class="text-p-base text-ink-gray-7">
            {{ answer.data.answer }}
          </p>
          <div
            v-else-if="answer.data.answer"
            class="flex flex-col gap-3 text-p-base text-ink-gray-8"
          >
            <p
              v-for="(paragraph, index) in paragraphs"
              :key="index"
              class="whitespace-pre-line break-words"
            >
              <template v-for="(part, i) in paragraph" :key="i">
                <PortalLink
                  v-if="part.source"
                  :to="ROUTES.article(part.source)"
                  :aria-label="part.source.title"
                  class="mx-0.5 inline-flex size-[18px] -translate-y-px items-center justify-center rounded-full bg-surface-gray-2 text-[11px] font-medium text-ink-gray-7 hover:bg-surface-gray-3 hover:text-ink-gray-9"
                >
                  {{ part.source.number }}
                </PortalLink>
                <template v-else>{{ part.text }}</template>
              </template>
            </p>
          </div>

          <div
            v-if="answer.data.sources.length"
            class="flex flex-wrap items-center gap-2"
          >
            <span class="text-p-sm text-ink-gray-5">{{ __("Sources") }}</span>
            <PortalLink
              v-for="source in answer.data.sources"
              :key="source.name"
              :to="ROUTES.article(source)"
              class="flex max-w-full items-center gap-1.5 rounded-full border border-outline-gray-2 py-1 pl-1.5 pr-3 text-p-sm text-ink-gray-7 hover:bg-surface-gray-1 hover:text-ink-gray-9"
            >
              <span
                class="flex size-[18px] shrink-0 items-center justify-center rounded-full bg-surface-gray-2 text-[11px] font-medium"
              >
                {{ source.number }}
              </span>
              <span class="truncate">{{ source.title }}</span>
            </PortalLink>
          </div>
        </div>

        <div v-if="answer.data.related.length" class="flex flex-col gap-3">
          <h2 class="text-p-sm font-medium text-ink-gray-6">
            {{ __("Related articles") }}
          </h2>
          <div class="rounded-6 border border-outline-gray-2 px-2.5">
            <PortalArticleList :articles="answer.data.related" />
          </div>
        </div>

        <p
          v-if="answer.data.answer && !answer.data.refused"
          class="text-p-sm text-ink-gray-5"
        >
          {{ __("AI can make mistakes. Check the linked articles.") }}
        </p>
      </section>
    </Transition>
  </div>
</template>

<script setup lang="ts">
import { computed, toRef } from "vue";
import LucideArrowLeft from "~icons/lucide/arrow-left";
import LucideSparkles from "~icons/lucide/sparkles";
import { ROUTES } from "@helpdesk/shared/portalRoutes";
import { __ } from "@helpdesk/shared/translation";
import PortalArticleList from "@app/components/knowledge_base/PortalArticleList.vue";
import PortalArticleSearch from "@app/components/knowledge_base/PortalArticleSearch.vue";
import PortalEmptyState from "@app/components/ui/PortalEmptyState.vue";
import PortalLink from "@app/components/ui/PortalLink.vue";
import { useAiAnswer } from "@app/composables/useAiAnswer";

type Source = {
  number: number;
  name: string;
  title: string;
  title_slug?: string;
};

const SKELETON_WIDTHS = ["100%", "92%", "78%"];
const CITATION = /\[(\d+)\]/g;

const props = defineProps<{ question: string }>();

const { answer, matches, isFailed, isLoading, showMatches } = useAiAnswer(
  toRef(props, "question")
);

// Each [n] becomes a link to its source; one the answer cites without a source is dropped.
const paragraphs = computed(() => {
  const sources: Source[] = answer.data?.sources || [];
  return String(answer.data?.answer || "")
    .split(/\n{2,}/)
    .map((paragraph) =>
      paragraph
        .split(CITATION)
        .map((text, index) =>
          index % 2
            ? {
                source: sources.find(
                  (source) => source.number === Number(text)
                ),
              }
            : { text }
        )
        .filter((part) => part.source || part.text)
    )
    .filter((parts) => parts.length);
});
</script>

<style scoped>
.answer-enter-active {
  transition: opacity 0.3s ease-out, transform 0.3s ease-out;
}
.answer-leave-active {
  transition: opacity 0.12s ease-in;
}
.answer-enter-from {
  opacity: 0;
  transform: translateY(6px);
}
.answer-leave-to {
  opacity: 0;
}
.thinking {
  animation: thinking 1.6s ease-in-out infinite;
}
@keyframes thinking {
  50% {
    opacity: 0.4;
  }
}
@media (prefers-reduced-motion: reduce) {
  .answer-enter-active,
  .answer-leave-active {
    transition: none;
  }
  .thinking {
    animation: none;
  }
}
</style>
