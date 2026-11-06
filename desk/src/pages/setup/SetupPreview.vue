<template>
  <div
    ref="panel"
    class="relative hidden flex-1 items-center justify-center overflow-hidden bg-surface-gray-1 lg:sticky lg:top-0 lg:flex lg:h-screen"
    aria-hidden="true"
  >
    <div
      class="relative size-[640px] shrink-0"
      :style="{ transform: `scale(${fit})` }"
    >
      <svg
        class="absolute inset-0 size-full overflow-visible text-ink-gray-7"
        viewBox="0 0 640 640"
        fill="none"
      >
        <path
          ref="dotted"
          :d="strandPath(0)"
          pathLength="100"
          stroke="currentColor"
          stroke-width="1.5"
          stroke-linecap="round"
          stroke-dasharray="0.01 1.6"
          class="text-ink-gray-4 transition-opacity duration-700"
          :class="mailbox ? 'opacity-0' : 'opacity-100'"
        />
        <path
          v-for="strand in strands"
          :key="strand.i"
          :d="strand.d"
          pathLength="100"
          stroke="currentColor"
          stroke-width="1"
          stroke-dasharray="100 100"
          :style="{
            opacity: strandOn(strand.i) ? strand.opacity : 0,
            strokeDashoffset: strandOn(strand.i) ? 0 : 100,
            transition: `stroke-dashoffset 1800ms cubic-bezier(.22,1,.36,1) ${strand.delay}ms, opacity 500ms ease ${strand.delay}ms`,
          }"
        />
        <path
          v-for="(comet, n) in COMETS"
          :key="'c' + n"
          :ref="(el) => (comets[n] = el as SVGPathElement)"
          :d="strandPath(comet.i)"
          pathLength="100"
          stroke="currentColor"
          :stroke-width="comet.width"
          stroke-linecap="round"
          stroke-dasharray="14 200"
          stroke-dashoffset="14"
          class="text-ink-gray-8"
          :style="{ opacity: strandOn(comet.i) ? 1 : 0 }"
        />

        <TransitionGroup
          tag="g"
          :css="false"
          @enter="fadeIn"
          @leave="fadeOut"
        >
          <g v-for="agent in agents" :key="agent.key">
            <path
              :d="agent.d"
              pathLength="100"
              stroke="currentColor"
              stroke-width="1.25"
              stroke-linecap="round"
              stroke-dasharray="0.01 2.4"
              class="text-ink-gray-4 transition-opacity duration-500"
              :class="agent.sent ? 'opacity-0' : 'opacity-100'"
            />
            <path
              :d="agent.d"
              pathLength="100"
              stroke="currentColor"
              stroke-width="0.75"
              stroke-dasharray="100 100"
              :style="{
                strokeDashoffset: agent.sent ? 0 : 100,
                transition: 'stroke-dashoffset 1200ms cubic-bezier(.22,1,.36,1)',
              }"
            />
            <path
              :data-root="agent.key"
              :d="agent.d"
              pathLength="100"
              stroke="currentColor"
              stroke-width="1.75"
              stroke-linecap="round"
              stroke-dasharray="16 200"
              stroke-dashoffset="16"
              class="text-ink-gray-8"
              :style="{ opacity: agent.sent ? 0.9 : 0.5 }"
            />
          </g>
        </TransitionGroup>
      </svg>

      <div
        class="absolute left-[56px] top-[54px] flex flex-col items-start gap-2"
      >
        <span ref="source" class="relative block h-10 w-14 shrink-0">
          <span
            v-if="mailbox && !arrived"
            class="absolute inset-0 animate-pulse rounded-4 border border-outline-gray-4 motion-reduce:animate-none"
          />
          <span
            class="absolute inset-0 overflow-hidden rounded-4 border transition-colors duration-700"
            :class="
              mailbox
                ? 'border-outline-gray-3 bg-surface-elevation-1 text-ink-gray-5 shadow-md'
                : 'border-dashed border-outline-gray-3 bg-surface-gray-1 text-ink-gray-3'
            "
          >
            <svg class="absolute inset-0 size-full" viewBox="0 0 56 40" fill="none">
              <path
                d="M1 3 L24.6 22 Q28 24.6 31.4 22 L55 3"
                stroke="currentColor"
                stroke-width="1.25"
                stroke-linecap="round"
                stroke-linejoin="round"
              />
            </svg>
          </span>
          <span
            class="absolute -bottom-1.5 -right-1.5 flex size-5 items-center justify-center rounded-full border transition-colors duration-700"
            :class="
              mailbox
                ? 'border-outline-gray-2 bg-surface-elevation-1 text-ink-gray-8'
                : 'border-dashed border-outline-gray-3 bg-surface-gray-1 text-ink-gray-4'
            "
          >
            <LucideMail v-if="mailbox" class="size-3" />
            <LucidePlus v-else class="size-3" />
          </span>
        </span>
        <Transition
          mode="out-in"
          enter-active-class="transition duration-500 ease-out motion-reduce:transition-none"
          enter-from-class="opacity-0 translate-x-1"
          leave-active-class="transition duration-150 motion-reduce:transition-none"
          leave-to-class="opacity-0"
        >
          <div :key="mailbox || 'none'" class="whitespace-nowrap">
            <p
              class="text-sm"
              :class="mailbox ? 'text-ink-gray-8' : 'text-ink-gray-5'"
            >
              {{ mailbox || __("Your support mailbox") }}
            </p>
          </div>
        </Transition>
      </div>

      <div ref="drift" class="absolute left-[176px] top-[176px] w-[360px]">
        <div
          class="absolute inset-0 origin-bottom-left rounded-5 border border-outline-gray-1 bg-surface-elevation-1 transition duration-1000 ease-[cubic-bezier(.22,1,.36,1)] motion-reduce:transition-none"
          :class="arrived ? '-rotate-[3.6deg] opacity-80' : 'rotate-0 opacity-0'"
        />
        <div
          class="absolute inset-0 origin-bottom-right rounded-5 border border-outline-gray-1 bg-surface-elevation-1 transition duration-1000 ease-[cubic-bezier(.22,1,.36,1)] motion-reduce:transition-none"
          :class="replied ? 'rotate-[2.6deg] opacity-90' : 'rotate-0 opacity-0'"
        />

        <div
          ref="sheet"
          class="relative rounded-5 border bg-surface-elevation-1 transition-[border-color,box-shadow] duration-1000 ease-out motion-reduce:transition-none"
          :class="
            arrived
              ? 'border-outline-gray-1 shadow-md'
              : 'border-dashed border-outline-gray-3 shadow-none'
          "
        >
          <div class="grid px-4 pb-3 pt-3.5">
            <div
              class="col-start-1 row-start-1 flex items-center gap-2 transition duration-700 motion-reduce:transition-none"
              :class="arrived ? 'translate-y-0 opacity-100' : 'translate-y-1 opacity-0'"
            >
              <span class="text-sm tabular-nums text-ink-gray-4">#1042</span>
              <span class="truncate text-base-semibold text-ink-gray-8">{{
                __("Can't reset my password")
              }}</span>
              <Badge
                :label="__('Open')"
                theme="gray"
                variant="subtle"
                class="ml-auto"
              />
            </div>
            <div
              class="col-start-1 row-start-1 flex animate-pulse items-center gap-2 transition-opacity duration-500 motion-reduce:animate-none"
              :class="arrived ? 'opacity-0' : 'opacity-100'"
            >
              <span class="h-2.5 w-9 rounded-full bg-surface-gray-2" />
              <span class="h-2.5 w-40 rounded-full bg-surface-gray-2" />
            </div>
          </div>

          <div class="space-y-4 px-4 pb-4">
            <div class="grid">
              <div
                class="col-start-1 row-start-1 flex items-start gap-2.5 transition duration-700 delay-200 motion-reduce:transition-none"
                :class="arrived ? 'translate-y-0 opacity-100' : 'translate-y-3 opacity-0'"
              >
                <Avatar
                  :label="__('Maya Fernandez')"
                  :image="avatarFor('maya-fernandez')"
                  size="md"
                />
                <div class="min-w-0 flex-1 space-y-0.5">
                  <div class="flex items-center gap-1.5">
                    <span class="text-sm-semibold text-ink-gray-8">{{
                      __("Maya Fernandez")
                    }}</span>
                    <LucideMail class="size-3 text-ink-gray-4" />
                    <span class="text-xs text-ink-gray-5">{{
                      __("2 min ago")
                    }}</span>
                  </div>
                  <p class="text-p-sm text-ink-gray-7">
                    {{
                      __(
                        "The reset link in the email says it has expired. Could you send me a new one?"
                      )
                    }}
                  </p>
                </div>
              </div>
              <div
                class="col-start-1 row-start-1 flex animate-pulse items-start gap-2.5 transition-opacity duration-500 motion-reduce:animate-none"
                :class="arrived ? 'opacity-0' : 'opacity-100'"
              >
                <span class="size-6 shrink-0 rounded-full bg-surface-gray-2" />
                <div class="flex-1 space-y-2 pt-1">
                  <span class="block h-2.5 w-24 rounded-full bg-surface-gray-2" />
                  <span class="block h-2.5 w-full rounded-full bg-surface-gray-1" />
                  <span class="block h-2.5 w-3/4 rounded-full bg-surface-gray-1" />
                </div>
              </div>
            </div>

            <div class="grid">
              <div
                class="col-start-1 row-start-1 flex items-start gap-2.5 transition duration-700 delay-300 motion-reduce:transition-none"
                :class="replied ? 'translate-y-0 opacity-100' : 'translate-y-3 opacity-0'"
              >
                <Avatar
                  :label="__('You')"
                  :image="avatarFor('helpdesk-you')"
                  size="md"
                />
                <div class="min-w-0 flex-1 space-y-0.5">
                  <div class="flex items-center gap-1.5">
                    <span class="text-sm-semibold text-ink-gray-8">{{
                      __("You")
                    }}</span>
                    <span class="text-xs text-ink-gray-5">{{
                      __("just now")
                    }}</span>
                  </div>
                  <p class="text-p-sm text-ink-gray-7">
                    {{ __("Here's a fresh link. It stays valid for 24 hours.") }}
                  </p>
                </div>
              </div>
              <p
                class="col-start-1 row-start-1 self-center pl-[34px] text-p-sm text-ink-gray-4 transition-opacity duration-500 motion-reduce:transition-none"
                :class="replied ? 'opacity-0' : 'opacity-100'"
              >
                {{ __("Your team replies here") }}
              </p>
            </div>
          </div>
        </div>
      </div>

      <span
        ref="ripple"
        class="absolute left-[350px] top-[170px] size-3 rounded-full border border-outline-gray-7 opacity-0"
      />

      <TransitionGroup
        tag="div"
        class="absolute inset-0"
        enter-active-class="transition duration-700 delay-200 ease-[cubic-bezier(.34,1.56,.64,1)] motion-reduce:transition-none"
        enter-from-class="opacity-0 scale-[.2]"
        leave-active-class="transition duration-200 motion-reduce:transition-none"
        leave-to-class="opacity-0 scale-75"
      >
        <div
          v-for="agent in agents"
          :key="agent.key"
          class="absolute -ml-10 -mt-4 flex w-20 flex-col items-center gap-1"
          :style="{ left: agent.x + 'px', top: agent.y + 'px' }"
        >
          <span
            v-if="agent.more"
            :data-agent="agent.key"
            class="flex size-8 items-center justify-center rounded-full bg-surface-gray-3 text-xs tabular-nums text-ink-gray-7"
          >
            +{{ agent.more }}
          </span>
          <span
            v-else
            :data-agent="agent.key"
            class="block transition-opacity duration-700"
            :class="agent.sent ? 'opacity-100' : 'opacity-70'"
          >
            <Avatar
              :label="agent.label"
              :image="avatarFor(agent.label)"
              size="xl"
            />
          </span>
          <span
            v-if="!agent.more"
            class="max-w-full truncate text-xs text-ink-gray-6"
            >{{ agent.name }}</span
          >
        </div>
      </TransitionGroup>

      <div class="absolute left-[56px] top-[528px] w-[224px]">
        <Transition
          mode="out-in"
          enter-active-class="transition duration-500 ease-out motion-reduce:transition-none"
          enter-from-class="opacity-0 translate-y-2"
          leave-active-class="transition duration-200 motion-reduce:transition-none"
          leave-to-class="opacity-0"
        >
          <div :key="caption.title" class="space-y-1">
            <p class="text-2xl-semibold text-ink-gray-8">{{ caption.title }}</p>
            <p class="text-p-sm text-ink-gray-5">{{ caption.sub }}</p>
          </div>
        </Transition>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { __ } from "@/translation";
import { useElementSize } from "@vueuse/core";
import { Avatar, Badge } from "frappe-ui";
import { computed, onBeforeUnmount, onMounted, ref, watch } from "vue";
import LucideMail from "~icons/lucide/mail";
import LucidePlus from "~icons/lucide/plus";
import { avatarFor } from "./avatars";
import { AGENT_SLOTS, STAGE, rootPath, strandPath } from "./previewPaths";

type Invitee = { email: string; sent: boolean };

const props = defineProps<{
  mailbox: string | null;
  arrived: boolean;
  invitees: Invitee[];
}>();

const reduced = !!window.matchMedia?.("(prefers-reduced-motion: reduce)")
  .matches;

const panel = ref<HTMLElement | null>(null);
const { width, height } = useElementSize(panel);
const fit = computed(() =>
  width.value
    ? Math.min(1.12, (width.value - 40) / STAGE, (height.value - 24) / STAGE)
    : 1
);

const team = computed(() => props.invitees.length > 0);
const replied = computed(() => props.arrived && team.value);

// One strand when connected, three with the first ticket, five with the team.
const INK = [0.85, 0.5, 0.3];
const strands = [-2, -1, 0, 1, 2].map((i) => ({
  i,
  d: strandPath(i),
  opacity: INK[Math.abs(i)] ?? 0.3,
  delay: Math.abs(i) * 180,
}));
const strandOn = (i: number) => {
  const level = Math.abs(i);
  if (level === 0) return !!props.mailbox;
  if (level === 1) return !!props.mailbox && props.arrived;
  return !!props.mailbox && props.arrived && team.value;
};

const agents = computed(() => {
  const all = props.invitees;
  const over = all.length > AGENT_SLOTS.length;
  const shown = over ? all.slice(0, AGENT_SLOTS.length - 1) : all;
  const out = shown.map((invitee, n) => {
    const [x, y] = AGENT_SLOTS[n]!;
    return {
      key: invitee.email,
      label: invitee.email,
      name: invitee.email.split("@")[0],
      sent: invitee.sent,
      x,
      y,
      d: rootPath(x, y),
      more: 0,
    };
  });
  if (over) {
    const rest = all.slice(AGENT_SLOTS.length - 1);
    const [x, y] = AGENT_SLOTS[AGENT_SLOTS.length - 1]!;
    out.push({
      key: "more",
      label: "",
      name: "more",
      sent: rest.every((invitee) => invitee.sent),
      x,
      y,
      d: rootPath(x, y),
      more: rest.length,
    });
  }
  return out;
});

const dotted = ref<SVGPathElement | null>(null);
const comets = ref<SVGPathElement[]>([]);
const COMETS = [
  { i: 0, width: 2, delay: 0 },
  { i: -1, width: 1.25, delay: 1600 },
];
const source = ref<HTMLElement | null>(null);
const ripple = ref<HTMLElement | null>(null);
const sheet = ref<HTMLElement | null>(null);
const drift = ref<HTMLElement | null>(null);
let loops: Animation[] = [];
let rootLoops: Animation[] = [];
let float: Animation | undefined;

function stopMotion() {
  loops.forEach((a) => a.cancel());
  loops = [];
}

function pulses(duration: number, landing: number) {
  comets.value.forEach((el, n) => {
    if (!el) return;
    loops.push(
      el.animate(
        [
          {
            offset: 0,
            strokeDashoffset: 14,
            easing: "cubic-bezier(.45,.05,.55,.95)",
          },
          { offset: landing, strokeDashoffset: -100 },
          { offset: 1, strokeDashoffset: -100 },
        ],
        {
          duration,
          iterations: Infinity,
          delay: COMETS[n]!.delay,
          fill: "backwards",
        }
      )
    );
  });
  if (source.value)
    loops.push(
      source.value.animate(
        [
          { offset: 0, transform: "scale(1)" },
          { offset: 0.05, transform: "scale(1.035)" },
          { offset: 0.16, transform: "scale(1)" },
          { offset: 1, transform: "scale(1)" },
        ],
        { duration, iterations: Infinity }
      )
    );
  if (!ripple.value) return;
  loops.push(
    ripple.value.animate(
      [
        { offset: 0, opacity: 0, transform: "scale(.4)" },
        { offset: landing - 0.03, opacity: 0, transform: "scale(.4)" },
        { offset: landing, opacity: 0.7, transform: "scale(.8)" },
        {
          offset: Math.min(landing + 0.24, 1),
          opacity: 0,
          transform: "scale(4.5)",
        },
        { offset: 1, opacity: 0, transform: "scale(4.5)" },
      ],
      { duration, iterations: Infinity }
    )
  );
}

function syncMotion() {
  stopMotion();
  if (reduced) return;
  if (!props.mailbox) {
    dotted.value &&
      loops.push(
        dotted.value.animate(
          [{ strokeDashoffset: 0 }, { strokeDashoffset: -3.2 }],
          { duration: 2200, iterations: Infinity }
        )
      );
    return;
  }
  // once live, the ribbon keeps a slow heartbeat
  if (props.arrived) pulses(9000, 0.3);
  else pulses(4600, 0.62);
}

function syncRoots() {
  rootLoops.forEach((a) => a.cancel());
  rootLoops = [];
  if (reduced || !panel.value) return;
  agents.value.forEach((agent, n) => {
    const beat = 2600;
    const options = {
      duration: beat * Math.max(agents.value.length, 2),
      iterations: Infinity,
      delay: n * beat,
      fill: "backwards" as const,
    };
    const share = beat / options.duration;
    const line = panel.value?.querySelector(`[data-root="${agent.key}"]`);
    const person = panel.value?.querySelector(`[data-agent="${agent.key}"]`);
    line &&
      rootLoops.push(
        line.animate(
          [
            {
              offset: 0,
              strokeDashoffset: 16,
              easing: "cubic-bezier(.45,.05,.4,.95)",
            },
            { offset: share * 0.8, strokeDashoffset: -100 },
            { offset: 1, strokeDashoffset: -100 },
          ],
          options
        )
      );
    person &&
      rootLoops.push(
        person.animate(
          [
            { offset: 0, transform: "scale(1)" },
            { offset: share * 0.74, transform: "scale(1)", easing: "ease-out" },
            { offset: share * 0.86, transform: "scale(1.08)" },
            { offset: share, transform: "scale(1)" },
            { offset: 1, transform: "scale(1)" },
          ],
          options
        )
      );
  });
}

watch(
  () => agents.value.map((agent) => agent.key + agent.sent).join(),
  syncRoots,
  { flush: "post" }
);
watch(() => [props.mailbox, props.arrived], syncMotion, { flush: "post" });

// Each new ticket stage lifts the paper a touch.
watch(
  () => props.arrived,
  (arrived) => {
    if (!arrived || reduced || !sheet.value) return;
    sheet.value.animate(
      [
        { transform: "translateY(14px) scale(.96)" },
        { transform: "translateY(-6px) scale(1.015)", offset: 0.55 },
        { transform: "translateY(0) scale(1)" },
      ],
      { duration: 1100, easing: "cubic-bezier(.22,1,.36,1)" }
    );
  }
);

onMounted(() => {
  syncMotion();
  syncRoots();
  if (reduced || !drift.value) return;
  float = drift.value.animate(
    [{ transform: "translateY(-4px)" }, { transform: "translateY(4px)" }],
    {
      duration: 5200,
      iterations: Infinity,
      direction: "alternate",
      easing: "ease-in-out",
    }
  );
});
onBeforeUnmount(() => {
  stopMotion();
  rootLoops.forEach((a) => a.cancel());
  float?.cancel();
});

function fadeIn(el: Element, done: () => void) {
  if (reduced) return done();
  el.animate([{ opacity: 0 }, { opacity: 1 }], {
    duration: 700,
    easing: "ease-out",
  }).onfinish = done;
}
function fadeOut(el: Element, done: () => void) {
  if (reduced) return done();
  el.animate([{ opacity: 1 }, { opacity: 0 }], { duration: 200 }).onfinish =
    done;
}

const caption = computed(() => {
  const count = props.invitees.length;
  if (count)
    return {
      title:
        count === 1
          ? __("1 agent joining")
          : __("{0} agents joining", [count]),
      sub: __("Every thread now has someone to answer it."),
    };
  if (props.arrived)
    return {
      title: __("Your first ticket"),
      sub: __("Every email to this address lands here."),
    };
  if (props.mailbox)
    return {
      title: __("Listening…"),
      sub: __("Send a test email and watch it arrive."),
    };
  return {
    title: __("Your helpdesk starts here"),
    sub: __("Connect a mailbox to bring it to life."),
  };
});
</script>
