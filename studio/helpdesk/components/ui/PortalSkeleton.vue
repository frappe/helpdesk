<template>
  <div
    :class="bare ? 'contents' : ['portal-skeleton', instant && 'is-instant']"
    :aria-busy="bare ? undefined : 'true'"
  >
    <span v-if="!bare" class="sr-only" role="status">{{ __("Loading") }}</span>

    <div
      v-if="variant === 'category-grid'"
      class="grid grid-cols-1 gap-[10px] sm:auto-rows-fr sm:grid-cols-2 lg:grid-cols-[repeat(var(--category-columns),minmax(0,1fr))]"
      :style="{ '--category-columns': columns }"
    >
      <div
        v-for="i in count"
        :key="i"
        class="flex flex-col gap-4 rounded-5 border border-outline-gray-2 p-5 max-sm:flex-row max-sm:gap-3 max-sm:px-4 max-sm:py-3.5"
      >
        <Skeleton :class="[BLOCK, 'size-5 shrink-0 rounded-4']" />
        <div class="flex min-w-0 flex-1 flex-col gap-1">
          <Line text="text-base-semibold" :width="width(i, 40)" />
          <div>
            <Line text="text-p-sm" width="90%" />
            <Line text="text-p-sm max-sm:hidden" :width="width(i + 2, 45)" />
          </div>
        </div>
      </div>
    </div>

    <div
      v-else-if="variant === 'article-rows'"
      class="flex flex-col rounded-[12px] border border-outline-gray-1"
    >
      <div
        v-for="i in count"
        :key="i"
        class="-mt-px flex items-center gap-2 border-t border-outline-gray-2 px-4 py-3 first:border-transparent sm:px-5"
      >
        <Skeleton :class="[BLOCK, 'size-4 shrink-0 rounded-4']" />
        <Line text="text-p-sm flex-1" :width="width(i, 35)" />
      </div>
    </div>

    <!-- count: the home's categories last time. One gets the lone-category layout, with no grid or sort tabs. -->
    <template v-else-if="variant === 'kb-home'">
      <div
        v-if="count !== 1"
        class="mx-auto flex w-full max-w-[832px] flex-col gap-5 px-4 pb-2 pt-8 sm:pb-4 sm:pt-[41px]"
      >
        <div class="flex h-7 items-center">
          <Line text="text-lg w-full" width="6rem" />
        </div>
        <PortalSkeleton
          variant="category-grid"
          :count="Math.min(count, 9)"
          :columns="count === 2 ? 2 : 3"
          bare
        />
      </div>
      <div
        class="mx-auto flex w-full max-w-[832px] flex-col gap-4 px-4 pt-8 sm:pt-[41px]"
      >
        <div v-if="count === 1" class="flex min-w-0 flex-col gap-1">
          <Line text="text-lg" width="9rem" />
          <Line text="text-p-base" width="min(20rem, 80%)" />
        </div>
        <div v-else class="flex h-7 items-center justify-between gap-4">
          <Line text="text-lg flex-1" width="5rem" />
          <Skeleton :class="[BLOCK, 'h-7 w-36 rounded-6']" />
        </div>
        <div class="pb-20">
          <PortalSkeleton variant="article-rows" :count="5" bare />
        </div>
      </div>
    </template>

    <div v-else-if="variant === 'category'" class="flex flex-col gap-6">
      <div class="flex flex-col gap-3">
        <Line text="text-3xl" width="12rem" />
        <Line text="text-p-base" width="18rem" />
        <div class="flex h-6 items-center gap-2">
          <Skeleton :class="[BLOCK, 'size-6 rounded-full']" />
          <Line text="text-p-sm" width="9rem" />
        </div>
      </div>
      <PortalSkeleton variant="category-rows" :count="count" bare />
    </div>

    <div v-else-if="variant === 'category-rows'" class="flex flex-col">
      <div
        v-for="i in count"
        :key="i"
        class="relative flex items-center gap-4 py-4 after:absolute after:inset-x-0 after:bottom-0 after:h-px after:bg-[--outline-gray-1] last:after:hidden"
      >
        <div class="flex min-w-0 flex-1 flex-col gap-0.5">
          <Line text="text-base" :width="width(i, 45)" />
          <Line text="text-p-sm" :width="width(i + 3, 70)" />
        </div>
        <Skeleton :class="[BLOCK, 'size-4 shrink-0 rounded-4']" />
      </div>
    </div>

    <div v-else-if="variant === 'article'" class="flex flex-col gap-6">
      <div class="flex flex-col gap-3 border-b border-outline-gray-1 pb-3.5">
        <Line
          text="text-4xl-semibold max-sm:!text-[24px]"
          width="min(28rem, 80%)"
        />
        <div class="flex h-6 items-center gap-2">
          <Skeleton :class="[BLOCK, 'size-6 shrink-0 rounded-full']" />
          <Line text="text-sm" width="14rem" />
        </div>
      </div>
      <div class="flex flex-col gap-4">
        <div v-for="p in 3" :key="p">
          <Line
            v-for="i in 3"
            :key="i"
            text="text-p-base"
            :width="i === 3 ? width(p, 40) : '100%'"
          />
        </div>
      </div>
    </div>

    <div v-else-if="variant === 'nav'" class="flex flex-col gap-0.5">
      <div
        v-for="i in count"
        :key="i"
        class="flex h-7 items-center gap-2 px-2 max-md:h-9"
      >
        <Skeleton :class="[BLOCK, 'size-4 shrink-0 rounded-4']" />
        <Line text="text-sm flex-1" :width="width(i, 40)" />
      </div>
    </div>

    <template v-else-if="variant === 'ticket'">
      <div class="relative flex min-w-0 flex-1 flex-col px-4 sm:px-6 lg:px-10">
        <PortalSkeleton variant="thread" bare />
        <div class="absolute inset-x-0 bottom-0 px-3 pb-3 sm:px-5 sm:pb-5">
          <div
            class="flex h-[38px] items-center gap-2 rounded-6 border border-outline-gray-2 bg-surface-gray-2 px-3.5"
          >
            <Skeleton :class="[BLOCK, 'size-5 shrink-0 rounded-full']" />
            <Line text="text-base flex-1" width="8rem" />
          </div>
        </div>
      </div>
      <div
        class="flex w-[352px] shrink-0 flex-col border-l border-outline-gray-2 max-lg:hidden"
      >
        <div class="flex flex-col gap-4 p-4">
          <div class="flex items-center gap-2.5">
            <Skeleton :class="[BLOCK, 'size-10 shrink-0 rounded-full']" />
            <div class="flex min-w-0 flex-1 flex-col">
              <Line text="text-xl" width="9rem" />
              <Line text="text-p-sm" width="3rem" />
            </div>
          </div>
          <div class="flex flex-col gap-2.5">
            <div
              v-for="i in 4"
              :key="i"
              class="flex min-h-7 items-center gap-2"
            >
              <Line text="text-base w-[106px] shrink-0" width="4.5rem" />
              <Line text="text-base flex-1" :width="width(i, 40)" />
            </div>
          </div>
        </div>
        <div class="border-t border-outline-gray-2">
          <div class="flex h-[47px] items-center px-4">
            <Line text="text-base w-full" width="4.5rem" />
          </div>
          <div class="px-4 pb-4 pt-0.5">
            <div
              v-for="i in 4"
              :key="i"
              class="grid min-h-14 grid-cols-[16px_minmax(0,1fr)] gap-3 last:min-h-0"
            >
              <div class="flex justify-center">
                <Skeleton :class="[BLOCK, 'mt-1.5 size-2 rounded-full']" />
              </div>
              <div>
                <Line text="text-base-medium" :width="width(i, 45)" />
                <Line text="text-p-xs" :width="width(i + 3, 35)" />
              </div>
            </div>
          </div>
        </div>
      </div>
    </template>

    <div
      v-else-if="variant === 'thread' && conversationLayout === 'chat'"
      class="flex flex-col gap-4 pt-6"
    >
      <div
        v-for="i in 3"
        :key="i"
        class="flex flex-col gap-1"
        :class="i === 2 ? 'items-end' : 'items-start'"
      >
        <Line text="text-p-sm w-28" width="100%" />
        <div
          class="w-[min(28rem,76%)] rounded-[10px] border border-outline-gray-2 px-3 py-1.5"
        >
          <Line text="text-p-base" width="100%" />
          <Line text="text-p-base" :width="width(i, 40)" />
        </div>
      </div>
    </div>
    <div v-else-if="variant === 'thread'" class="flex flex-col gap-6 pt-6">
      <div v-for="i in 2" :key="i" class="flex gap-2.5">
        <Skeleton :class="[BLOCK, 'size-7 shrink-0 rounded-full']" />
        <div class="min-w-0 flex-1 rounded-[10px] border border-outline-gray-2">
          <div
            class="flex h-10 items-center justify-between gap-4 border-b border-outline-gray-1 px-3"
          >
            <Line text="text-base w-24" width="100%" />
            <Line text="text-p-sm w-16" width="100%" />
          </div>
          <div class="p-3">
            <Line
              v-for="line in i === 1 ? 3 : 2"
              :key="line"
              text="text-p-base"
              :width="line === (i === 1 ? 3 : 2) ? width(i, 40) : '100%'"
            />
          </div>
        </div>
      </div>
    </div>

    <div v-else-if="variant === 'form'" class="flex w-full flex-col">
      <div class="flex flex-col gap-5">
        <div class="flex flex-col gap-1.5">
          <Line text="text-xs" width="3.5rem" />
          <Skeleton :class="[BLOCK, 'h-7 w-full rounded-[8px]']" />
        </div>
        <div class="flex flex-col gap-1.5">
          <Line text="text-p-sm" width="4.5rem" />
          <div class="h-[164px] rounded-6 border border-outline-gray-2">
            <div
              class="flex h-9 items-center gap-2.5 border-b border-outline-gray-2 px-2"
            >
              <Skeleton
                v-for="i in 8"
                :key="i"
                :class="[BLOCK, 'size-4 rounded-4']"
              />
            </div>
          </div>
        </div>
        <div class="grid grid-cols-1 gap-4 sm:grid-cols-3">
          <div v-for="i in 6" :key="i" class="flex flex-col gap-1.5">
            <Line text="text-xs" :width="width(i, 30)" />
            <Skeleton :class="[BLOCK, 'h-7 w-full rounded-[8px]']" />
          </div>
        </div>
        <div
          class="h-[58px] rounded-6 border border-dashed border-outline-gray-2"
        />
      </div>
      <div class="flex justify-end pb-8 pt-8 sm:pt-[39px]">
        <Skeleton :class="[BLOCK, 'h-8 w-28 rounded-[8px]']" />
      </div>
    </div>

    <div v-else-if="variant === 'profile'" class="flex flex-col">
      <div class="flex items-center gap-4 pt-1.5">
        <Skeleton :class="[BLOCK, 'size-16 shrink-0 rounded-full']" />
        <div class="flex flex-col gap-1">
          <div class="flex min-h-7 items-center">
            <Line text="text-2xl-semibold w-40" width="100%" />
          </div>
          <Line text="text-p-sm w-48" width="100%" />
        </div>
      </div>
      <div class="mt-8 flex h-7 items-center">
        <Line text="text-base w-full" width="6rem" />
      </div>
      <div class="mt-2">
        <PortalSkeleton variant="settings-rows" :count="4" bare />
      </div>
      <div class="mt-4"><Line text="text-base" width="4.5rem" /></div>
      <div class="mt-2">
        <PortalSkeleton variant="settings-rows" :count="1" bare />
      </div>
    </div>

    <div v-else-if="variant === 'settings-rows'" class="flex flex-col">
      <div
        v-for="i in count"
        :key="i"
        class="flex h-[68px] items-center justify-between gap-4"
      >
        <div class="flex min-w-0 flex-1 flex-col gap-1">
          <Line text="text-base-medium" :width="`${4.5 + (i % 3)}rem`" />
          <Line text="text-p-sm" :width="width(i, 40)" />
        </div>
        <Skeleton :class="[BLOCK, 'h-7 w-32 shrink-0 rounded-[8px]']" />
      </div>
    </div>

    <div v-else-if="variant === 'filters'" class="flex items-center gap-2">
      <Skeleton
        v-for="i in count"
        :key="i"
        :class="[
          BLOCK,
          'h-7 w-40 rounded-[8px]',
          i === 1 ? 'max-sm:flex-1' : 'max-lg:hidden',
        ]"
      />
    </div>

    <slot v-else />
  </div>
</template>

<script setup lang="ts">
import { h, type FunctionalComponent } from "vue";
import { Skeleton } from "frappe-ui";
import { __ } from "@helpdesk/shared/translation";
// Relative, not `@app/`: the desk's new-ticket form renders this.
import { conversationLayout } from "../../stores/conversationLayout";

defineOptions({ name: "PortalSkeleton" });

withDefaults(
  defineProps<{
    variant?:
      | "category-grid"
      | "article-rows"
      | "kb-home"
      | "category"
      | "category-rows"
      | "article"
      | "nav"
      | "filters"
      | "ticket"
      | "thread"
      | "form"
      | "profile"
      | "settings-rows";
    count?: number;
    columns?: number;
    // Nested: the parent already announces loading.
    bare?: boolean;
    // Replaces an on-screen skeleton, so skip the fade-in delay.
    instant?: boolean;
  }>(),
  { count: 6, columns: 3 }
);

const BLOCK = "motion-reduce:animate-none";

const WIDTHS = [72, 58, 84, 64, 90, 52, 78, 68];
function width(index: number, floor: number) {
  const value = WIDTHS[index % WIDTHS.length];
  return `${Math.max(value, floor)}%`;
}

const Line: FunctionalComponent<{ text: string; width: string }> = (props) =>
  h("div", { class: ["relative", props.text] }, [
    " ",
    h(Skeleton, {
      class: `${BLOCK} absolute start-0 top-1/2 h-[0.6em] -translate-y-1/2 rounded-full`,
      style: { width: props.width },
    }),
  ]);
Line.props = ["text", "width"];
</script>

<style>
/* `backwards`, not `both`: a held opacity fill traps drawers under their backdrop. */
.portal-skeleton {
  animation: portal-fade-in 200ms ease-out 150ms backwards;
}
.portal-skeleton.is-instant {
  animation: none;
}
.portal-reveal {
  animation: portal-fade-in 180ms ease-out backwards;
}
@keyframes portal-fade-in {
  from {
    opacity: 0;
  }
}
@media (prefers-reduced-motion: reduce) {
  .portal-skeleton,
  .portal-reveal {
    animation: none;
  }
}
</style>
