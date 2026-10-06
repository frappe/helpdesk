<template>
  <nav
    :aria-label="__('Categories')"
    class="flex flex-col border-t border-outline-gray-1"
  >
    <RouterLink
      v-for="category in categories"
      :key="category.name"
      :to="ROUTES.category(category.name)"
      class="flex items-center gap-4 border-b border-outline-gray-1 py-4 transition-colors hover:bg-surface-gray-1"
    >
      <div class="flex min-w-0 flex-1 flex-col gap-1">
        <span class="truncate text-lg font-medium text-ink-gray-9">
          {{ category.category_name }}
        </span>
        <span
          v-if="hasDescription(category)"
          class="truncate text-base text-ink-gray-5"
        >
          {{ category.description }}
        </span>
        <span
          class="mt-1 flex flex-wrap items-center gap-2 text-sm text-ink-gray-5"
        >
          <template v-if="category.creators?.length">
            <span class="flex ps-1.5">
              <Avatar
                v-for="creator in category.creators"
                :key="creator.name"
                class="-ms-1.5 ring-2 ring-[var(--surface-base)]"
                shape="circle"
                size="md"
                :image="creator.image"
                :label="creator.name"
              />
            </span>
            <span>{{ creatorLabel(category) }}</span>
            <span class="text-ink-gray-3">·</span>
          </template>
          <span class="text-ink-gray-9">
            {{
              countLabel(
                category.article_count,
                __("1 article"),
                __("{0} articles")
              )
            }}
          </span>
        </span>
      </div>
      <LucideChevronRight class="size-4 shrink-0 text-ink-gray-4" />
    </RouterLink>
  </nav>
</template>

<script setup lang="ts">
import { Avatar } from "frappe-ui";
import LucideChevronRight from "~icons/lucide/chevron-right";
import { __ } from "@helpdesk/shared/translation";
import { ROUTES } from "@app/routes";
import { countLabel } from "@app/utils";

type Category = {
  name: string;
  category_name: string;
  description?: string | null;
  article_count: number;
  creators?: { name: string; image: string | null }[];
  creator_count?: number;
};

defineProps<{ categories: Category[] }>();

// The cards' stand-in for a missing description says nothing in a list.
function hasDescription(category: Category) {
  const text = category.description?.trim();
  return Boolean(text) && text !== "Browse articles in this category";
}

function creatorLabel(category: Category) {
  const first = category.creators![0].name.split(" ")[0];
  const others = (category.creator_count ?? 1) - 1;
  if (!others) return __("By {0}", [first]);
  if (others === 1) return __("By {0} and 1 other", [first]);
  return __("By {0} and {1} others", [first, others]);
}
</script>
