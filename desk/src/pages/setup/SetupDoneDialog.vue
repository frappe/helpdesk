<template>
  <Dialog :open="open" bare size="md" @update:open="(v) => !v && close(false)">
    <div class="overflow-hidden rounded-6">
      <div
        class="flex h-[168px] justify-center overflow-hidden bg-surface-gray-1"
        aria-hidden="true"
      >
        <div class="relative h-[168px] w-[400px] shrink-0">
          <svg
            class="absolute inset-0 size-full overflow-visible text-ink-gray-6"
            viewBox="0 0 400 168"
            fill="none"
          >
            <mask id="setup-done-ribbon">
              <path
                :d="RIBBON"
                pathLength="100"
                stroke="white"
                stroke-width="6"
                stroke-dasharray="100 100"
                :style="stroke(80)"
              />
            </mask>
            <path
              :d="RIBBON"
              stroke="currentColor"
              stroke-width="1.75"
              stroke-linecap="round"
              stroke-dasharray="0 5"
              mask="url(#setup-done-ribbon)"
            />
            <path
              v-for="(r, n) in RAYS"
              :key="'r' + n"
              :d="r.d"
              pathLength="100"
              stroke="currentColor"
              stroke-width="1.25"
              stroke-linecap="round"
              stroke-dasharray="100 100"
              class="text-ink-gray-4"
              :style="stroke(r.delay, 500)"
            />
            <path
              v-for="p in people"
              :key="p.email"
              :d="p.d"
              pathLength="100"
              stroke="currentColor"
              stroke-width="1"
              stroke-dasharray="100 100"
              :style="stroke(p.delay - 200, 800)"
            />
          </svg>

          <span
            class="absolute left-[28px] top-[64px] h-10 w-14 overflow-hidden rounded-4 border text-ink-gray-5"
            :class="
              connected
                ? 'border-outline-gray-3 bg-surface-elevation-1 shadow-sm'
                : 'border-dashed border-outline-gray-3 bg-surface-gray-1'
            "
            :style="pop(0)"
          >
            <svg
              class="absolute inset-0 size-full"
              viewBox="0 0 56 40"
              fill="none"
            >
              <path
                d="M1 3 L24.6 22 Q28 24.6 31.4 22 L55 3"
                stroke="currentColor"
                stroke-width="1.25"
                stroke-linecap="round"
              />
            </svg>
          </span>

          <div
            class="absolute left-[160px] top-[46px] h-[76px] w-20"
            :style="pop(620)"
          >
            <span
              class="absolute inset-0 -rotate-6 rounded-4 border border-outline-gray-1 bg-surface-elevation-1"
            />
            <span
              class="absolute inset-0 rotate-[4deg] rounded-4 border border-outline-gray-1 bg-surface-elevation-1"
            />
            <span
              class="absolute inset-0 flex flex-col gap-1.5 rounded-4 border border-outline-gray-2 bg-surface-elevation-1 p-2.5 shadow-md"
            >
              <span class="h-1 w-10 rounded-full bg-surface-gray-3" />
              <span class="h-1 w-7 rounded-full bg-surface-gray-2" />
              <span class="mt-auto flex justify-end">
                <span
                  class="flex size-7 items-center justify-center rounded-full bg-surface-gray-9"
                >
                  <svg
                    class="size-4 text-ink-gray-1"
                    viewBox="0 0 16 16"
                    fill="none"
                  >
                    <path
                      d="M3.5 8.5 L6.8 11.5 L12.5 4.8"
                      pathLength="100"
                      stroke="currentColor"
                      stroke-width="2"
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      stroke-dasharray="100 100"
                      :style="stroke(980, 450)"
                    />
                  </svg>
                </span>
              </span>
            </span>
          </div>

          <span
            v-for="p in people"
            :key="p.email"
            class="absolute -ml-4 -mt-4"
            :style="{ left: p.x + 'px', top: p.y + 'px', ...pop(p.delay) }"
          >
            <Avatar :label="p.email" :image="avatarUrl(p.email)" size="xl" />
          </span>
          <span
            v-if="extra"
            class="absolute left-[362px] top-[136px] flex size-7 items-center justify-center rounded-full bg-surface-gray-3 text-xs tabular-nums text-ink-gray-7"
            :style="pop(1900)"
          >
            +{{ extra }}
          </span>
        </div>
      </div>

      <div class="space-y-5 bg-surface-elevation-2 p-6">
        <div class="space-y-1.5 text-center">
          <h2 class="text-3xl text-ink-gray-9">{{ __("You're all set") }}</h2>
          <p class="text-p-base text-ink-gray-6">{{ summary }}</p>
        </div>

        <template v-if="askFeedback">
          <div
            class="flex flex-col items-center gap-2 border-t border-outline-gray-1 pt-5"
          >
            <p class="text-base text-ink-gray-7">
              {{ __("How was setting up Helpdesk?") }}
            </p>
            <Rating v-model="rating" />
          </div>

          <div
            class="grid transition-[grid-template-rows,opacity] duration-500 ease-out motion-reduce:transition-none"
            :class="
              rating
                ? 'grid-rows-[1fr] opacity-100'
                : 'grid-rows-[0fr] opacity-0'
            "
          >
            <div class="min-h-0 overflow-hidden">
              <FormControl
                v-model="comment"
                type="textarea"
                :label="__('Anything we could improve? (optional)')"
                :rows="3"
                :maxlength="MAX_COMMENT"
                :disabled="!rating"
              />
              <p
                v-if="comment.length"
                class="mt-1 text-right text-xs tabular-nums text-ink-gray-5"
              >
                {{ comment.length }}/{{ MAX_COMMENT }}
              </p>
            </div>
          </div>

          <div class="flex justify-end gap-2">
            <Button
              variant="outline"
              :label="__('Not now')"
              @click="close(false)"
            />
            <Button
              variant="solid"
              theme="gray"
              :label="__('Submit')"
              :disabled="!rating"
              @click="close(true)"
            />
          </div>
        </template>
        <Button
          v-else
          variant="solid"
          theme="gray"
          size="md"
          class="w-full"
          :label="__('Go to Helpdesk')"
          @click="close(false)"
        />
      </div>
    </div>
  </Dialog>
</template>

<script setup lang="ts">
import { capture } from "@/telemetry";
import { avatarUrl } from "./preview";
import { __ } from "@/translation";
import { Avatar, Button, Dialog, FormControl, Rating, toast } from "frappe-ui";
import { computed, nextTick, onMounted, ref, watch } from "vue";

const props = defineProps<{
  open: boolean;
  connected: boolean;
  agents: string[];
  askFeedback: boolean;
}>();
const emit = defineEmits<{ close: [] }>();

const MAX_COMMENT = 500;
const rating = ref(0);
const comment = ref("");
const reducedMotion = !!window.matchMedia?.("(prefers-reduced-motion: reduce)")
  .matches;

const drawn = ref(reducedMotion);
function play() {
  if (reducedMotion) return;
  drawn.value = false;
  nextTick(() =>
    requestAnimationFrame(() =>
      requestAnimationFrame(() => (drawn.value = true))
    )
  );
}
watch(
  () => props.open,
  (open) => open && play()
);
onMounted(() => props.open && play());

const RIBBON = "M 70 84 C 104 56, 132 112, 176 84";

const PLACES = [
  [318, 48],
  [352, 84],
  [318, 120],
];
const people = computed(() =>
  props.agents.slice(0, PLACES.length).map((email, n) => {
    const [x, y] = PLACES[n];
    return {
      email,
      x,
      y,
      d: `M 224 84 C 258 84, ${x - 44} ${y}, ${x} ${y}`,
      delay: 1250 + n * 150,
    };
  })
);
const extra = computed(() => Math.max(0, props.agents.length - PLACES.length));

const RAYS = Array.from({ length: 12 }, (_, n) => {
  const angle = (n / 12) * Math.PI * 2 + Math.PI / 12;
  const inner = 62;
  const outer = n % 2 ? 72 : 78;
  const point = (r: number) =>
    `${200 + Math.cos(angle) * r * 0.92} ${84 + Math.sin(angle) * r * 0.72}`;
  return {
    d: `M ${point(inner)} L ${point(outer)}`,
    delay: 1050 + (n % 4) * 40,
    side: Math.abs(Math.cos(angle)) > 0.9,
  };
}).filter((r) => !r.side);

const summary = computed(() => {
  const n = props.agents.length;
  if (props.connected && n)
    return n === 1
      ? __("Your mailbox is connected and 1 agent invited.")
      : __("Your mailbox is connected and {0} agents invited.", [n]);
  if (props.connected)
    return __("Your mailbox is connected. New emails will become tickets.");
  if (n)
    return n === 1
      ? __("1 agent invited. You can connect email from Settings.")
      : __("{0} agents invited. You can connect email from Settings.", [n]);
  return __("You can connect email and invite agents any time from Settings.");
});

const stroke = (delay: number, ms = 1100) => ({
  strokeDashoffset: drawn.value ? 0 : 100,
  transition: drawn.value
    ? `stroke-dashoffset ${ms}ms cubic-bezier(.22,1,.36,1) ${delay}ms`
    : "none",
});
const pop = (delay: number) => ({
  transform: drawn.value ? "scale(1)" : "scale(.5)",
  opacity: drawn.value ? 1 : 0,
  transition: drawn.value
    ? `transform 650ms cubic-bezier(.34,1.56,.64,1) ${delay}ms, opacity 250ms ease ${delay}ms`
    : "none",
});

function close(submit: boolean) {
  if (submit) {
    capture("setup_feedback", {
      data: { rating: rating.value, comment: comment.value.trim() },
    });
    toast.success(__("Thanks for the feedback"));
  }
  emit("close");
}
</script>
