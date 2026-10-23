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
        <div class="flex items-center justify-between gap-4">
          <Line
            text="text-4xl-semibold max-sm:!text-[24px] flex-1"
            width="min(28rem, 80%)"
          />
          <Skeleton
            :class="[
              BLOCK,
              'mt-1 h-6 w-[136px] shrink-0 self-start rounded-[8px] max-sm:hidden',
            ]"
          />
        </div>
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
      <div class="relative flex min-w-0 flex-1 flex-col">
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
          <div class="flex items-center gap-3">
            <Skeleton :class="[BLOCK, 'size-[46px] shrink-0 rounded-full']" />
            <div class="flex min-w-0 flex-1 flex-col gap-1.5">
              <Line text="text-md" width="9rem" />
              <Line text="text-p-sm" width="3rem" />
            </div>
          </div>
          <div class="flex flex-col gap-2.5">
            <div
              v-for="i in 3"
              :key="i"
              class="flex min-h-7 items-center gap-2"
            >
              <Line
                text="text-base me-[9px] w-[106px] shrink-0"
                width="4.5rem"
              />
              <Line text="text-base flex-1" :width="width(i, 40)" />
            </div>
          </div>
        </div>
        <!-- The Timeline section, so nothing pops in below on load. -->
        <div class="border-t border-outline-gray-2">
          <div class="flex items-center px-4 py-3.5">
            <Line text="text-base" width="4.5rem" />
          </div>
          <div class="px-4 pb-4 pt-0.5">
            <PortalSkeleton variant="timeline-steps" :count="5" bare />
          </div>
        </div>
      </div>
    </template>

    <!-- The viewer's conversation layout: chat bubbles, or email cards. -->
    <!-- PortalTicketThread's gutters, so the page skeleton and its own line up. -->
    <div
      v-else-if="variant === 'thread'"
      class="flex flex-col pt-4"
      :class="
        conversationLayout === 'chat'
          ? 'px-3 sm:px-5'
          : 'max-sm:px-4 sm:px-6 lg:px-10'
      "
    >
      <!-- PortalChatList's rows: a bubble, then the name and time under it. A bubble
           is 12px of padding plus 22px per line of its iframe; messages run 1 to 3 lines. -->
      <div v-if="conversationLayout === 'chat'" class="flex flex-col gap-3">
        <div
          v-for="(bubble, i) in CHAT_BUBBLES"
          :key="i"
          class="flex gap-2"
          :class="i % 2 ? '' : 'flex-row-reverse'"
        >
          <Skeleton
            v-if="i % 2"
            :class="[BLOCK, 'size-7 shrink-0 rounded-full']"
          />
          <div
            class="flex max-w-[80%] flex-col gap-1"
            :class="i % 2 ? 'items-start' : 'items-end'"
            :style="{ width: bubble.width }"
          >
            <Skeleton
              :class="[BLOCK, 'w-full rounded-6']"
              :style="{ height: `${12 + 22 * bubble.lines}px` }"
            />
            <!-- The viewer's own messages show only the time. -->
            <Line
              :text="i % 2 ? 'mx-1 w-28 text-xs' : 'mx-1 w-14 text-xs'"
              width="100%"
            />
          </div>
        </div>
      </div>
      <!-- ActivityTimeline's rows: mt-2 on the list, the avatar 6px into its card. -->
      <div v-else class="mt-2 flex flex-col gap-4">
        <div v-for="i in 2" :key="i" class="flex gap-2.5">
          <Skeleton :class="[BLOCK, 'mt-1.5 size-7 shrink-0 rounded-full']" />
          <div class="flex-1 rounded-[8px] border border-outline-gray-2">
            <div class="flex h-10 items-center justify-between gap-4 px-3">
              <Line text="text-base w-24" width="100%" />
              <Line text="text-sm w-20" width="100%" />
            </div>
            <div class="border-t border-outline-gray-2 p-3">
              <Line text="text-base" :width="width(i, 60)" />
              <Line v-if="i === 1" text="text-base" width="40%" />
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- PortalTicketTimeline's rows: 16px rail, 56px steps. -->
    <div v-else-if="variant === 'timeline-steps'" class="flex flex-col">
      <div
        v-for="i in count"
        :key="i"
        class="grid grid-cols-[16px_minmax(0,1fr)] gap-3"
      >
        <div class="flex justify-center">
          <Skeleton :class="[BLOCK, 'mt-1.5 size-2 rounded-full']" />
        </div>
        <div :class="i < count && 'min-h-14'">
          <Line text="text-base-medium" :width="width(i, 45)" />
          <Line text="text-p-xs" :width="width(i + 3, 35)" />
        </div>
      </div>
    </div>

    <!-- count: the template's fields last time. -->
    <div v-else-if="variant === 'form'" class="flex w-full flex-col">
      <div class="flex flex-col gap-5">
        <div class="flex flex-col gap-1.5">
          <Line text="text-xs" width="3.5rem" />
          <Skeleton :class="[BLOCK, 'h-7 w-full rounded-[8px]']" />
        </div>
        <div class="flex flex-col gap-1.5">
          <Line text="text-p-sm" width="4.5rem" />
          <div class="h-[228px] rounded-6 border border-outline-gray-2">
            <div
              class="flex h-9 items-center gap-3.5 overflow-hidden border-b border-outline-gray-2 px-2"
            >
              <Skeleton
                v-for="i in 24"
                :key="i"
                :class="[BLOCK, 'size-4 shrink-0 rounded-4']"
              />
            </div>
          </div>
        </div>
        <div v-if="count" class="grid grid-cols-1 gap-4 sm:grid-cols-3">
          <div v-for="i in count" :key="i" class="flex flex-col gap-1.5">
            <Line text="text-xs" :width="width(i, 30)" />
            <Skeleton :class="[BLOCK, 'h-7 w-full rounded-[8px]']" />
          </div>
        </div>
        <div class="flex flex-col gap-1.5">
          <Line text="text-p-sm" width="5rem" />
          <div
            class="h-[68px] rounded-6 border border-dashed border-outline-gray-2"
          />
        </div>
      </div>
      <div class="flex justify-end pb-8 pt-8 sm:pt-[39px]">
        <Skeleton :class="[BLOCK, 'h-8 w-[105px] rounded-[8px]']" />
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
      <h2 class="mt-8 flex h-7 items-center text-md-semibold text-ink-gray-8">
        {{ __("Preferences") }}
      </h2>
      <div class="mt-2">
        <PortalSkeleton variant="settings-rows" :count="4" bare />
      </div>
      <h2 class="mt-11 text-md-semibold text-ink-gray-8">
        {{ __("Security") }}
      </h2>
      <div class="mt-2">
        <PortalSkeleton variant="settings-rows" :count="1" bare />
      </div>
    </div>

    <!-- Settings' organization screen. count: organizations last time; one opens directly. -->
    <div
      v-else-if="variant === 'organization'"
      class="flex min-h-0 flex-1 flex-col"
    >
      <div class="flex shrink-0 flex-col gap-1 px-4 py-5 sm:px-10 sm:py-8">
        <Line text="text-lg" width="11rem" />
        <Line text="text-base" width="min(17rem, 80%)" />
      </div>
      <div class="min-h-0 flex-1 overflow-hidden px-4 pb-5 sm:px-10">
        <template v-if="count === 1">
          <div class="flex items-center gap-4 pt-1.5">
            <Skeleton :class="[BLOCK, 'size-16 shrink-0 rounded-[12px]']" />
            <Line text="text-2xl-semibold w-40" width="100%" />
          </div>
          <div class="mt-5 flex h-[29px] gap-6 border-b border-outline-gray-2">
            <Line text="text-base w-16" width="100%" />
            <Line text="text-base w-12" width="100%" />
          </div>
          <Skeleton :class="[BLOCK, 'mt-7 h-7 w-full rounded-[8px]']" />
          <div class="mt-3 flex min-h-8 items-center">
            <Line text="text-p-xs w-10" width="100%" />
          </div>
          <div
            v-for="i in 3"
            :key="i"
            class="flex min-h-13 items-center gap-2 border-t border-outline-gray-1 py-2.5"
          >
            <Skeleton :class="[BLOCK, 'size-8 shrink-0 rounded-full']" />
            <div class="flex h-[39px] flex-1 flex-col justify-center gap-2">
              <Skeleton
                :class="[BLOCK, 'h-2.5 rounded-full']"
                :style="{ width: width(i, 30) }"
              />
              <Skeleton
                :class="[BLOCK, 'h-2 rounded-full']"
                :style="{ width: width(i + 3, 45) }"
              />
            </div>
          </div>
        </template>
        <template v-else>
          <Skeleton :class="[BLOCK, 'mb-6 h-7 w-full rounded-[8px]']" />
          <div
            class="grid grid-cols-[repeat(auto-fill,minmax(210px,1fr))] gap-3"
          >
            <div
              v-for="i in Math.min(count, 9)"
              :key="i"
              class="rounded-[10px] border border-outline-gray-2 p-4"
            >
              <Skeleton :class="[BLOCK, 'mb-3 size-12 rounded-[10px]']" />
              <Line text="text-base" width="60%" />
              <Line text="text-p-sm mt-0.5" width="40%" />
              <div
                class="mt-3 flex h-[33px] items-end border-t border-outline-gray-1"
              >
                <Skeleton :class="[BLOCK, 'mb-1 h-2 w-4/5 rounded-full']" />
              </div>
            </div>
          </div>
        </template>
      </div>
    </div>

    <div
      v-else-if="variant === 'settings-rows'"
      class="flex flex-col divide-y divide-outline-gray-1"
    >
      <div
        v-for="i in count"
        :key="i"
        class="flex items-center justify-between gap-8 py-3.5"
      >
        <div class="flex min-w-0 flex-1 flex-col gap-1">
          <Line
            text="text-base-medium h-[17px]"
            :width="`${4.5 + (i % 3)}rem`"
          />
          <Line text="text-base leading-5" :width="width(i, 40)" />
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
// Relative, not @app: the desk imports this through NewTicketForm.
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
      | "timeline-steps"
      | "thread"
      | "form"
      | "profile"
      | "settings-rows"
      | "organization";
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

const CHAT_BUBBLES = [
  { width: "16rem", lines: 1 },
  { width: "22rem", lines: 3 },
  { width: "18rem", lines: 2 },
];

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
