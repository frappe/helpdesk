<template>
  <Transition
    enter-active-class="transition duration-200 ease-out motion-reduce:transition-none"
    enter-from-class="-translate-y-1 opacity-0"
    leave-active-class="transition duration-150 ease-in motion-reduce:transition-none"
    leave-to-class="-translate-y-1 opacity-0"
  >
    <section v-if="articles?.length" class="flex flex-col">
      <span class="pb-1 text-p-sm text-ink-gray-5">
        {{
          __(
            "You may find the solution to your problem in one of these articles. Take a look before submitting a ticket."
          )
        }}
      </span>
      <!-- v-html: the server escapes the text and leaves only the search <mark> tags. -->
      <TransitionGroup
        enter-active-class="transition-opacity duration-200 motion-reduce:transition-none"
        enter-from-class="opacity-0"
      >
        <div
          v-for="article in articles"
          :key="article.name"
          class="border-outline-gray-1 [&:not(:last-child)]:border-b [&_mark]:bg-transparent [&_mark]:text-ink-gray-9"
        >
          <button
            type="button"
            class="group flex w-full items-center gap-3 py-3 text-left"
            :aria-expanded="open === article.name"
            @click="open = open === article.name ? null : article.name"
          >
            <span
              class="min-w-0 flex-1 text-base text-ink-gray-7 group-hover:text-ink-gray-9"
              v-html="article.title"
            />
            <span
              v-if="article.minutes"
              class="shrink-0 text-p-sm text-ink-gray-4"
            >
              {{ __("{0} min read", [article.minutes]) }}
            </span>
            <LucideChevronDown
              class="size-4 shrink-0 text-ink-gray-4 transition-transform duration-200"
              :class="{ 'rotate-180': open === article.name }"
            />
          </button>
          <!-- Rows grow from 0fr to 1fr so the height animates without measuring. -->
          <div
            class="grid transition-[grid-template-rows,opacity] duration-200 ease-out motion-reduce:transition-none"
            :class="
              open === article.name
                ? 'grid-rows-[1fr] opacity-100'
                : 'grid-rows-[0fr] opacity-0'
            "
            :inert="open !== article.name"
          >
            <div class="min-h-0 overflow-hidden">
              <div class="flex flex-col gap-3 pb-4">
                <p
                  class="text-p-base text-ink-gray-5"
                  v-html="article.excerpt"
                />
                <div class="flex items-center justify-between gap-4">
                  <div v-if="canGiveFeedback" class="flex items-center gap-1">
                    <span class="pr-1 text-p-sm text-ink-gray-8">{{
                      __("Helpful?")
                    }}</span>
                    <button
                      v-for="answer in ANSWERS"
                      :key="answer.value"
                      type="button"
                      :aria-label="answer.label"
                      :aria-pressed="
                        feedbackByArticle[article.name] === answer.value
                      "
                      class="grid size-7 place-items-center rounded-4 text-ink-gray-8 hover:bg-surface-gray-2"
                      @click="giveFeedback(article.name, answer.value)"
                    >
                      <PortalFeedbackThumb
                        :answer="answer.value"
                        :filled="
                          feedbackByArticle[article.name] === answer.value
                        "
                        background="var(--surface-base)"
                        class="size-4"
                      />
                    </button>
                  </div>
                  <a
                    class="ml-auto flex items-center gap-1 text-base text-ink-gray-6 hover:text-ink-gray-8"
                    :href="router.resolve(ROUTES.article(article)).href"
                    target="_blank"
                    rel="noopener"
                  >
                    {{ __("Read full article") }}
                    <LucideArrowUpRight class="size-4" />
                  </a>
                </div>
              </div>
            </div>
          </div>
        </div>
      </TransitionGroup>
    </section>
  </Transition>
</template>

<script setup lang="ts">
import { reactive, ref } from "vue";
import { useRouter } from "vue-router";
import { __ } from "@helpdesk/shared/translation";
import PortalFeedbackThumb from "@app/components/knowledge_base/PortalFeedbackThumb.vue";
import { ROUTES } from "@helpdesk/shared/portalRoutes";
import { useSession } from "@app/stores/session";
import {
  feedbackAnswers,
  saveArticleFeedback,
} from "@app/components/knowledge_base/articleFeedback";
import LucideArrowUpRight from "~icons/lucide/arrow-up-right";
import LucideChevronDown from "~icons/lucide/chevron-down";

const ANSWERS = feedbackAnswers();

defineProps<{
  articles?:
    | { name: string; title: string; excerpt?: string; minutes?: number }[]
    | null;
}>();

const router = useRouter();
const { canGiveFeedback } = useSession();
const open = ref<string | null>(null);
const feedbackByArticle = reactive<Record<string, number>>({});

function giveFeedback(article: string, answer: number) {
  return saveArticleFeedback(
    article,
    feedbackByArticle[article],
    answer,
    (value) => (feedbackByArticle[article] = value)
  );
}
</script>
