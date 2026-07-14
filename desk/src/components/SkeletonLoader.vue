<template>
  <div
    class="transition-all animate-fade-in duration-300 relative"
    :class="{ 'animate-pulse': loading }"
  >
    <slot name="number-cards">
      <div v-if="showVariant('number-cards')" :class="numberCardsGridClass">
        <!-- Vertical: title → value → subtitle stacked top→bottom -->
        <div
          v-if="orientation === 'vertical'"
          v-for="i in numberCardsCount"
          :key="`card-${i}`"
          class="border rounded-md p-4 space-y-3 max-h-[140px] min-h-[114px]"
        >
          <div class="h-3 w-1/2 bg-surface-gray-3 rounded" />
          <div class="h-7 w-2/3 bg-surface-gray-1 rounded" />
          <div class="h-3 w-1/2 bg-surface-gray-1 rounded" />
        </div>
        <!-- Horizontal: title on top, value + mini chart side-by-side, percentage row -->
        <div
          v-else
          v-for="i in numberCardsCount"
          :key="`card-h-${i}`"
          class="border rounded-md flex flex-col p-4 pt-3 gap-2"
          :style="{ minHeight: height }"
        >
          <div class="h-4 w-1/2 bg-surface-gray-3 rounded" />
          <div class="flex items-end w-full gap-2 justify-between flex-1">
            <div class="h-7 w-10 bg-surface-gray-2 rounded" />
            <div
              class="h-full max-w-[50%] w-[50%] flex items-end justify-end gap-1"
            >
              <div
                v-for="(h, idx) in barHeights"
                :key="idx"
                :style="{ height: `${h}%` }"
                class="w-2 bg-surface-gray-3 rounded-t-sm"
              />
            </div>
          </div>
          <div class="h-3 w-1/3 bg-surface-gray-2 rounded" />
        </div>
      </div>
    </slot>
    <slot name="bar-chart">
      <div
        v-if="showVariant('bar-chart')"
        :class="
          barChartCount !== 1 ? 'grid grid-cols-1 md:grid-cols-2 gap-4' : ''
        "
      >
        <div
          v-for="i in barChartCount"
          :key="`chart-${i}`"
          class="border rounded-md min-h-[300px] p-4 space-y-3"
        >
          <div class="h-4 w-1/3 bg-surface-gray-3 rounded" />
          <div class="h-4 w-1/4 bg-surface-gray-1 rounded" />

          <div
            class="h-64 w-full rounded flex items-center justify-center relative overflow-hidden"
          >
            <div
              class="absolute inset-0 flex items-end justify-center px-[33px] py-[23px] gap-10"
            >
              <div
                class="absolute inset-x-[33px] inset-y-[23px] left-[50px] flex flex-col justify-between pointer-events-none"
              >
                <div
                  v-for="j in 5"
                  :key="j"
                  class="border-t border-dotted border-[var(--ink-gray-3)]"
                />
              </div>
              <div
                v-for="(height, idx) in barHeights"
                :key="idx"
                :style="{ height: `${height}%` }"
                class="w-[30px] rounded-sm bg-[var(--surface-gray-3)] shrink-0 z-10"
              />
              <!-- x-y labels -->

              <div
                class="absolute left-0 hidden md:flex flex-col justify-between inset-x-[33px] inset-y-[23px]"
              >
                <div
                  v-for="j in 5"
                  :key="j"
                  class="h-[10px] w-[28px] rounded-sm bg-[var(--surface-gray-3)]"
                />
              </div>
              <div class="absolute flex justify-center bottom-0 gap-10">
                <div
                  v-for="j in barHeights.length"
                  :key="j"
                  class="h-[10px] w-[30px] rounded-sm bg-[var(--surface-gray-3)]"
                />
              </div>
            </div>

            <!-- empty state -->
            <div
              v-if="showVariant('empty-state')"
              :style="{
                backgroundImage:
                  'radial-gradient(ellipse at center, var(--surface-base) 10%, color-mix(in srgb, var(--surface-base) 90%, transparent) 25%, transparent 70%)',
              }"
              class="rounded-xl p-6 w-2/3 text-center pointer-events-auto space-y-0.5 relative z-10 bottom-4.5"
            >
              <div
                class="relative z-10 text-ink-gray-7 text-center text-p-base-medium leading-[1.15]"
              >
                {{ __(getEmptyState(i).title) }}
              </div>
              <div
                class="relative z-10 text-ink-gray-6 text-center text-p-base"
              >
                {{
                  hasAppliedFilter
                    ? __(getEmptyState(i).filterMessage)
                    : __(getEmptyState(i).message)
                }}
              </div>
            </div>
          </div>
        </div>
      </div>
    </slot>
  </div>
</template>

<script setup>
import { useSlots } from "vue";

const props = defineProps({
  variants: {
    type: Array,
    default: () => ["number-cards", "bar-chart"],
  },
  numberCardsCount: { type: Number, default: 5 },
  // "vertical": title → value → subtitle stacked (default, KPI tiles).
  // "horizontal": title on top, value + mini chart side-by-side, percentage row (compact chart cards).
  orientation: {
    type: String,
    default: "vertical",
    validator: (v) => ["vertical", "horizontal"].includes(v),
  },
  numberCardsGridClass: {
    type: String,
    default: "grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4",
  },
  // Min-height of each card in the horizontal number-cards layout (any CSS length).
  height: {
    type: String,
    default: "160px",
  },
  barChartCount: { type: Number, default: 4 },
  barHeights: { type: Array, default: () => [63, 95, 44, 37, 70] },
  hasAppliedFilter: { type: Boolean, default: false },
  loading: { type: Boolean, default: false },
  emptyStates: {
    type: Array,
    default: () => [],
  },
});

const slots = useSlots();

const defaultEmptyStateMsg = {
  title: "No tickets found",
  message:
    "Dashboard charts will appear here once you start receiving or creating tickets.",
  filterMessage:
    "Based on the selected filters no tickets found. Try adjusting the date range or filters applied.",
};

function getEmptyState(index) {
  const entry = props.emptyStates[index - 1] ?? {};
  return { ...defaultEmptyStateMsg, ...entry };
}
function showVariant(slotName) {
  return !slots[slotName] && props.variants.includes(slotName);
}
</script>
