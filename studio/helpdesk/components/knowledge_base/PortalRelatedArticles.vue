<template>
  <Transition
    enter-active-class="transition duration-200 ease-out motion-reduce:transition-none"
    enter-from-class="-translate-y-1 opacity-0"
    leave-active-class="transition duration-150 ease-in motion-reduce:transition-none"
    leave-to-class="-translate-y-1 opacity-0"
  >
    <section
      v-if="articles?.length"
      class="flex flex-wrap items-center gap-x-1.5 gap-y-1"
    >
      <span class="shrink-0 text-p-sm text-ink-gray-5">
        {{ __("Related articles:") }}
      </span>
      <ul class="contents">
        <li
          v-for="(article, i) in articles"
          :key="article.name"
          class="flex min-w-0 items-center"
        >
          <!-- Hover delay stops cards flashing; below so it won't cover the next link. -->
          <HoverCard
            side="bottom"
            align="start"
            :offset="8"
            :hover-delay="250"
            :leave-delay="120"
          >
            <template #trigger>
              <a
                class="group flex max-w-64 items-center rounded-sm text-p-sm text-ink-gray-6 outline-none hover:text-ink-gray-9 focus-visible:ring-2 focus-visible:ring-outline-gray-3 data-[state=open]:text-ink-gray-9 [&_mark]:bg-transparent [&_mark]:font-medium [&_mark]:text-inherit"
                :href="articleHref(article)"
                target="_blank"
                rel="noopener"
              >
                <!-- v-html: server escapes all but the search <mark> tags. -->
                <span
                  class="truncate underline-offset-2 group-hover:underline group-data-[state=open]:underline"
                  v-html="article.title"
                />
              </a>
            </template>

            <a
              class="flex w-80 flex-col overflow-hidden rounded-lg outline-none [&_mark]:rounded-sm [&_mark]:bg-surface-amber-2 [&_mark]:px-0.5 [&_mark]:text-ink-gray-9"
              :href="articleHref(article)"
              target="_blank"
              rel="noopener"
              tabindex="-1"
            >
              <img
                v-if="article.image"
                :src="article.image"
                alt=""
                class="h-28 w-full object-cover"
              />
              <div class="flex flex-col gap-2 p-3">
                <span
                  v-if="article.category_name"
                  class="text-xs font-medium uppercase tracking-wide text-ink-gray-5"
                >
                  {{ article.category_name }}
                </span>
                <span
                  class="text-base font-semibold leading-snug text-ink-gray-9"
                  v-html="article.title"
                />
                <p
                  v-if="article.excerpt"
                  class="line-clamp-4 text-p-sm text-ink-gray-6"
                  v-html="article.excerpt"
                />
                <div
                  class="flex items-center justify-between pt-1 text-p-sm text-ink-gray-5"
                >
                  <span v-if="article.minutes">
                    {{ __("{0} min read", [article.minutes]) }}
                  </span>
                  <span class="ml-auto flex items-center gap-1 text-ink-gray-8">
                    {{ __("Open article") }}
                    <LucideArrowUpRight class="size-3.5" />
                  </span>
                </div>
              </div>
            </a>
          </HoverCard>
          <!-- Outside the link so the comma isn't underlined. -->
          <span v-if="i < articles.length - 1" class="text-p-sm text-ink-gray-5"
            >,</span
          >
        </li>
      </ul>
    </section>
  </Transition>
</template>

<script setup lang="ts">
import { HoverCard } from "frappe-ui";
import { useRouter } from "vue-router";
import { __ } from "@helpdesk/shared/translation";
import { ROUTES } from "@helpdesk/shared/portalRoutes";
import LucideArrowUpRight from "~icons/lucide/arrow-up-right";

type Article = {
  name: string;
  title: string;
  excerpt?: string;
  image?: string;
  minutes?: number;
  category_name?: string;
};

defineProps<{ articles?: Article[] | null }>();

const router = useRouter();

function articleHref(article: Article) {
  return router.resolve(ROUTES.article(article)).href;
}
</script>
