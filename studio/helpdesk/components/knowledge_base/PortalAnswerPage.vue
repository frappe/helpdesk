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
        :placeholder="__('Search again')"
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
          <span class="thinking-glyph text-base leading-none" aria-hidden="true">
            ✦
          </span>
          <Transition name="step" mode="out-in">
            <span :key="thinkingStep">{{ THINKING_STEPS[thinkingStep] }}</span>
          </Transition>
        </p>
        <div class="flex flex-col gap-2.5" aria-hidden="true">
          <div
            v-for="(width, index) in SKELETON_WIDTHS"
            :key="width"
            class="thinking h-3.5 rounded-full bg-surface-gray-2"
            :style="{ width, animationDelay: `${index * 0.15}s` }"
          />
        </div>
      </section>

      <section v-else-if="isEmpty" key="empty">
        <PortalEmptyState
          :title="__('What are you looking for?')"
          :description="__('Type a question in the search box above.')"
        />
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
              ? __("Something went wrong on our side. These articles may help.")
              : __("Something went wrong on our side. Please try again later.")
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
        <div class="flex flex-col gap-3">
          <h1 class="break-words text-xl font-semibold text-ink-gray-9">
            {{ question }}
          </h1>
          <template v-if="answer.data.refused">
            <p class="text-p-base text-ink-gray-7">
              {{ answer.data.message }}
            </p>
            <Button
              v-if="canRaiseTicket"
              class="w-fit"
              variant="subtle"
              icon-left="lucide-plus"
              :label="__('Raise a ticket')"
              @click="raiseTicket"
            />
          </template>
          <p v-else class="text-p-sm text-ink-gray-5">
            {{ __("The closest matches from the help center, by meaning.") }}
          </p>
        </div>

        <div v-if="answer.data.related.length" class="flex flex-col gap-3">
          <h2 class="text-p-sm font-medium text-ink-gray-6">
            {{ __("Related articles") }}
          </h2>
          <div class="rounded-6 border border-outline-gray-2 px-2.5">
            <PortalArticleList :articles="answer.data.related" />
          </div>
        </div>

        <div v-if="answer.data.links?.length" class="flex flex-col gap-3">
          <h2 class="text-p-sm font-medium text-ink-gray-6">
            {{ __("From the docs") }}
          </h2>
          <ul
            class="divide-y divide-outline-gray-1 rounded-6 border border-outline-gray-2"
          >
            <li v-for="link in answer.data.links" :key="link.url">
              <a
                :href="link.url"
                target="_blank"
                rel="noopener noreferrer"
                class="flex items-center gap-3 px-4 py-3 text-base text-ink-gray-8 hover:bg-surface-gray-1 focus-visible:focus-ring"
              >
                <LucideGlobe class="size-4 shrink-0 text-ink-gray-5" />
                <span class="min-w-0 flex-1 truncate">
                  {{ prettyUrl(link.url) }}
                </span>
                <LucideArrowUpRight class="size-4 shrink-0 text-ink-gray-4" />
              </a>
            </li>
          </ul>
        </div>

        <p
          class="flex items-center gap-1.5 text-xs text-ink-gray-5"
          data-testid="powered-by-flow"
        >
          <LucideWorkflow class="size-3" />
          {{ __("Search powered by Frappe Flow") }}
        </p>
      </section>
    </Transition>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, toRef, watch } from "vue";
import { useRouter } from "vue-router";
import { useIntervalFn } from "@vueuse/core";
import { Button } from "frappe-ui";
import LucideArrowLeft from "~icons/lucide/arrow-left";
import LucideArrowUpRight from "~icons/lucide/arrow-up-right";
import LucideGlobe from "~icons/lucide/globe";
import LucideWorkflow from "~icons/lucide/workflow";
import { ROUTES } from "@helpdesk/shared/portalRoutes";
import { __ } from "@helpdesk/shared/translation";
import PortalArticleList from "@app/components/knowledge_base/PortalArticleList.vue";
import PortalArticleSearch from "@app/components/knowledge_base/PortalArticleSearch.vue";
import PortalEmptyState from "@app/components/ui/PortalEmptyState.vue";
import PortalLink from "@app/components/ui/PortalLink.vue";
import { useAiAnswer } from "@app/composables/useAiAnswer";
import { useSession } from "@app/stores/session";

const SKELETON_WIDTHS = ["100%", "92%", "78%"];
const THINKING_STEPS = [
  __("Reading the help center…"),
  __("Finding the closest articles…"),
  __("Ranking the results…"),
];
const THINKING_STEP_MS = 1400;

const props = defineProps<{ question: string }>();

const router = useRouter();
const session = useSession();
const { answer, matches, isEmpty, isFailed, isLoading, showMatches } = useAiAnswer(
  toRef(props, "question")
);

// The status line moves on while the search runs, so a slow one still feels alive.
const thinkingStep = ref(0);
const { pause, resume } = useIntervalFn(
  () =>
    (thinkingStep.value = Math.min(
      thinkingStep.value + 1,
      THINKING_STEPS.length - 1
    )),
  THINKING_STEP_MS,
  { immediate: false }
);
watch(
  isLoading,
  (loading) => {
    thinkingStep.value = 0;
    if (loading) resume();
    else pause();
  },
  { immediate: true }
);

const canRaiseTicket = computed(
  () => !session.config.value?.hide_raise_ticket_button
);

function prettyUrl(url: string) {
  return url.replace(/^https?:\/\//, "").replace(/\/$/, "");
}

function raiseTicket() {
  if (session.isGuest.value) return session.signIn();
  router.push(ROUTES.newTicket({ from: "search", q: props.question }));
}
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
.step-enter-active,
.step-leave-active {
  transition: opacity 0.2s ease;
}
.step-enter-from,
.step-leave-to {
  opacity: 0;
}
.thinking {
  animation: thinking 1.6s ease-in-out infinite;
}
.thinking-glyph {
  display: inline-block;
  animation: glyph 2.4s ease-in-out infinite;
}
@keyframes thinking {
  50% {
    opacity: 0.4;
  }
}
@keyframes glyph {
  50% {
    opacity: 0.45;
    transform: scale(0.85) rotate(45deg);
  }
}
@media (prefers-reduced-motion: reduce) {
  .answer-enter-active,
  .answer-leave-active,
  .step-enter-active,
  .step-leave-active {
    transition: none;
  }
  .thinking,
  .thinking-glyph {
    animation: none;
  }
}
</style>
