<template>
  <div
    ref="stage"
    class="relative h-screen w-full overflow-hidden bg-surface-gray-1"
    aria-hidden="true"
    inert
  >
    <div
      class="absolute -right-40 -top-40 size-[640px] rounded-full bg-surface-violet-2 opacity-40 blur-[140px]"
    />
    <div
      class="absolute -bottom-48 -left-24 size-[560px] rounded-full bg-surface-blue-2 opacity-30 blur-[140px]"
    />

    <div
      class="absolute top-0 flex h-[72px] items-center"
      :style="{ left: box.left + 'px' }"
    >
      <Transition v-bind="fade">
        <span :key="String(isPortal)" class="text-base text-ink-gray-6">
          {{
            isPortal ? __("What your customers see") : __("What your team sees")
          }}
        </span>
      </Transition>
    </div>

    <div
      class="absolute"
      :style="{
        left: box.left + 'px',
        top: box.top + 'px',
        width: box.width + 'px',
        height: box.height + 'px',
      }"
    >
      <div
        class="origin-top-left"
        :style="{
          width: W + 'px',
          height: H + 'px',
          transform: `scale(${scale})`,
        }"
      >
        <div
          class="absolute inset-x-12 -top-7 h-full rounded-[16px] border border-outline-gray-2 bg-surface-gray-2 opacity-60"
        />
        <div
          class="absolute inset-x-6 -top-3.5 h-full rounded-[16px] border border-outline-gray-2 bg-surface-gray-2"
        />

        <div
          class="absolute inset-0 flex flex-col overflow-hidden rounded-[16px] border border-outline-gray-2 bg-surface-base shadow-2xl"
        >
          <div
            class="relative flex h-11 shrink-0 items-end gap-1 bg-surface-gray-2 px-3"
          >
            <span
              class="absolute bottom-0 h-9 w-[240px] rounded-t-[10px] bg-surface-base transition-[left] duration-500 ease-[cubic-bezier(.22,1,.36,1)] motion-reduce:transition-none"
              :style="{ left: 84 + (isPortal ? 244 : 0) + 'px' }"
            />
            <div class="flex h-full items-center gap-2 pe-4 ps-1">
              <span
                v-for="light in TRAFFIC_LIGHTS"
                :key="light"
                class="size-3 rounded-full border border-black/10"
                :class="light"
              />
            </div>
            <div
              v-for="t in tabs"
              :key="t.key"
              class="relative flex h-9 w-[240px] items-center gap-2 px-3"
            >
              <span
                class="flex size-4 shrink-0 items-center justify-center overflow-hidden rounded-[4px] text-[9px] font-semibold"
                :class="setup.brandLogo ? 'dark:bg-white' : ''"
              >
                <img
                  v-if="setup.brandLogo"
                  :src="setup.brandLogo"
                  alt=""
                  class="size-full object-cover"
                />
                <HDLogo v-else class="size-full" />
              </span>
              <Transition v-bind="fade">
                <span
                  :key="t.desk ? t.title : t.key"
                  class="min-w-0 flex-1 truncate text-sm transition-colors duration-500"
                  :class="t.active ? 'text-ink-gray-8' : 'text-ink-gray-5'"
                >
                  {{ t.title }}
                </span>
              </Transition>
              <span
                class="lucide-x size-3.5 text-ink-gray-5 transition-opacity duration-500"
                :class="t.active ? 'opacity-100' : 'opacity-0'"
              />
            </div>
            <span
              class="lucide-plus mb-2.5 ms-1 size-4 self-end text-ink-gray-6"
            />
          </div>
          <div
            class="flex h-11 shrink-0 items-center gap-4 border-b border-outline-gray-1 px-4"
          >
            <span class="lucide-arrow-left size-4 text-ink-gray-4" />
            <span class="lucide-arrow-right size-4 text-ink-gray-4" />
            <span class="lucide-rotate-cw size-4 text-ink-gray-4" />
            <div
              class="flex h-7 flex-1 items-center gap-2 rounded-full bg-surface-gray-2 px-3"
            >
              <span class="lucide-lock size-3.5 text-ink-gray-5" />
              <Transition v-bind="fade">
                <span :key="url" class="text-sm text-ink-gray-7">{{
                  url
                }}</span>
              </Transition>
              <span class="lucide-star ms-auto size-3.5 text-ink-gray-5" />
            </div>
            <Avatar
              :label="authStore.userName"
              :image="avatarUrl(authStore.userId)"
              size="sm"
            />
            <span class="lucide-ellipsis-vertical size-4 text-ink-gray-5" />
          </div>

          <div class="relative min-h-0 flex-1 overflow-hidden">
            <Transition v-bind="slide">
              <div
                v-if="page === 'login'"
                key="login"
                class="h-full bg-surface-base"
              >
                <div class="w-[840px] pt-[60px]">
                  <div class="mx-auto flex w-[400px] flex-col gap-5 p-6">
                    <div class="flex flex-col items-start gap-4">
                      <img :src="FRAPPE_LOGO" alt="" class="size-8" />
                      <div class="flex flex-col gap-1.5">
                        <p class="text-3xl font-bold text-ink-gray-9">
                          {{ __("Sign In") }}
                        </p>
                        <p class="text-p-base text-ink-gray-6">
                          {{ __("Welcome! Please sign in to continue.") }}
                        </p>
                      </div>
                    </div>
                    <div class="flex flex-col gap-8">
                      <div class="flex flex-col gap-4">
                        <div class="flex flex-col gap-1.5">
                          <p class="text-base text-ink-gray-5">
                            {{ __("Email") }}
                          </p>
                          <div
                            class="flex h-7 items-center rounded-4 border border-outline-gray-2 bg-surface-base px-2 text-base text-ink-gray-8"
                          >
                            {{ authStore.userId }}
                          </div>
                        </div>
                        <div class="flex flex-col gap-2">
                          <div class="flex flex-col gap-1.5">
                            <p class="text-base text-ink-gray-5">
                              {{ __("Password") }}
                            </p>
                            <div
                              class="flex h-7 items-center gap-[3px] rounded-4 border border-outline-gray-4 bg-surface-base px-2"
                            >
                              <TransitionGroup
                                enter-active-class="transition duration-150"
                                enter-from-class="scale-0"
                              >
                                <span
                                  v-for="n in passwordDots"
                                  :key="n"
                                  class="size-[5px] rounded-full bg-surface-gray-8"
                                />
                              </TransitionGroup>
                              <span
                                class="ms-px h-3.5 w-px animate-pulse bg-surface-gray-9 motion-reduce:animate-none"
                              />
                              <span
                                class="lucide-eye ms-auto size-4 text-ink-gray-5"
                              />
                            </div>
                          </div>
                          <p class="text-end text-base text-ink-gray-5">
                            {{ __("Forgot password?") }}
                          </p>
                        </div>
                      </div>
                      <Button variant="solid" class="w-full" tabindex="-1">
                        {{ __("Continue") }}
                      </Button>
                    </div>
                  </div>
                </div>
              </div>

              <SetupPreviewDesk v-else-if="isDesk" key="desk" :page="page" />

              <div
                v-else
                key="portal"
                class="relative flex h-full w-[840px] flex-col"
              >
                <header
                  class="flex h-14 shrink-0 items-center gap-2.5 border-b border-outline-gray-1 px-8"
                >
                  <span
                    class="flex size-7 items-center justify-center overflow-hidden rounded-[7px] text-base-semibold"
                    :class="setup.brandLogo ? 'dark:bg-white' : ''"
                  >
                    <img
                      v-if="setup.brandLogo"
                      :src="setup.brandLogo"
                      alt=""
                      class="size-full object-cover"
                    />
                    <HDLogo v-else class="size-full" />
                  </span>
                  <span class="text-lg-medium text-ink-gray-9">{{
                    brand
                  }}</span>
                  <div class="ms-auto flex items-center gap-5 text-base">
                    <span class="text-ink-gray-7">{{
                      __("Knowledge base")
                    }}</span>
                    <span class="text-ink-gray-7">{{ __("My tickets") }}</span>
                    <span class="lucide-moon size-4 text-ink-gray-6" />
                    <Button
                      variant="solid"
                      theme="gray"
                      icon-left="lucide-plus"
                      :label="__('Raise a ticket')"
                      tabindex="-1"
                    />
                  </div>
                </header>
                <Transition
                  enter-active-class="transition duration-500 ease-[cubic-bezier(.22,1,.36,1)] motion-reduce:transition-none"
                  enter-from-class="opacity-0 translate-y-3"
                  leave-active-class="absolute inset-x-0 transition duration-200 motion-reduce:transition-none"
                  leave-to-class="opacity-0"
                >
                  <div v-if="page === 'home'" key="home">
                    <div
                      class="relative overflow-hidden bg-surface-gray-1 px-10 pb-16 pt-20 text-center"
                    >
                      <div
                        class="absolute inset-0 text-ink-gray-2 opacity-70 bg-[repeating-linear-gradient(135deg,currentColor_0,currentColor_1px,transparent_1px,transparent_12px)]"
                      />
                      <div class="relative space-y-3">
                        <p
                          class="text-[34px] font-semibold leading-[1.15] text-ink-gray-9"
                        >
                          {{ __("Here's what might help") }}
                        </p>
                        <p class="text-p-lg text-ink-gray-6">
                          {{
                            __(
                              "Explore answers to frequently asked questions about"
                            )
                          }}
                          <span class="text-ink-gray-9">{{ brand }}</span
                          >.
                        </p>
                        <div
                          class="mx-auto !mt-7 flex h-12 max-w-[520px] items-center gap-2.5 rounded-6 border border-outline-gray-2 bg-surface-base px-4 text-start text-base text-ink-gray-4 shadow-lg"
                        >
                          <span class="lucide-search size-4" />
                          <span class="flex-1">{{
                            __(
                              "Search articles (e.g. billing, integration, or general)"
                            )
                          }}</span>
                          <span
                            class="rounded-1 border border-outline-gray-2 px-1.5 text-sm text-ink-gray-5"
                          >
                            /
                          </span>
                        </div>
                      </div>
                    </div>
                    <div
                      class="mx-auto flex max-w-[832px] flex-col gap-5 px-4 pt-8"
                    >
                      <div
                        class="flex min-h-7 items-center justify-between gap-4"
                      >
                        <p class="text-lg font-semibold text-ink-gray-9">
                          {{ __("Categories") }}
                        </p>
                        <Button
                          variant="ghost"
                          class="-mr-2"
                          :label="__('View all')"
                          tabindex="-1"
                        />
                      </div>
                      <div class="grid grid-cols-3 gap-[10px]">
                        <div
                          v-for="c in CATEGORIES"
                          :key="c.title"
                          class="flex flex-col gap-4 rounded-5 border border-outline-gray-2 p-5"
                        >
                          <span :class="[c.icon, 'size-5 text-ink-gray-6']" />
                          <div class="flex min-w-0 flex-col gap-1">
                            <p class="text-base-semibold text-ink-gray-9">
                              {{ c.title }}
                            </p>
                            <p class="line-clamp-2 text-p-sm text-ink-gray-6">
                              {{ c.description }}
                            </p>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>

                  <div v-else key="ticket" class="flex min-h-0 flex-1">
                    <div class="flex min-w-0 flex-1 flex-col px-10 pt-6">
                      <div class="flex items-center gap-1.5 text-lg">
                        <span class="text-ink-gray-5">{{
                          __("My tickets")
                        }}</span>
                        <span class="text-ink-gray-4">/</span>
                        <span class="truncate text-ink-gray-9">{{
                          SAMPLE_TICKET.subject
                        }}</span>
                      </div>
                      <div
                        class="mx-auto mt-10 flex w-full max-w-[600px] flex-col gap-6"
                      >
                        <div
                          class="flex max-w-[80%] flex-col items-end gap-1 self-end"
                        >
                          <div
                            class="rounded-6 bg-surface-gray-2 px-3.5 py-2.5 text-p-base text-ink-gray-9"
                          >
                            {{ SAMPLE_TICKET.message[1] }}
                          </div>
                          <span class="px-1 text-sm text-ink-gray-5">
                            {{ __("You · {0}", ["10:42"]) }}
                          </span>
                        </div>
                        <Transition
                          enter-active-class="transition duration-700 ease-out"
                          enter-from-class="opacity-0 translate-y-2"
                        >
                          <div
                            v-if="replied && agent"
                            class="flex max-w-[80%] flex-col items-start gap-1"
                          >
                            <div
                              class="rounded-6 border border-outline-gray-2 px-3.5 py-2.5 text-p-base text-ink-gray-9"
                            >
                              {{ SAMPLE_TICKET.reply.join(" ") }}
                            </div>
                            <span class="px-1 text-sm text-ink-gray-5">
                              {{ nameOf(agent.email) }} · 10:44
                            </span>
                          </div>
                        </Transition>
                        <div
                          class="mt-6 flex items-center gap-2 rounded-6 border border-outline-gray-2 p-2 ps-3.5"
                        >
                          <span class="flex-1 text-base text-ink-gray-4">
                            {{ __("Write a reply") }}
                          </span>
                          <span
                            class="lucide-paperclip size-4 text-ink-gray-5"
                          />
                          <Button
                            variant="solid"
                            theme="gray"
                            :label="__('Send')"
                            tabindex="-1"
                          />
                        </div>
                      </div>
                    </div>
                    <aside
                      class="w-[280px] shrink-0 space-y-4 border-l border-outline-gray-1 p-5"
                    >
                      <p class="text-base-semibold text-ink-gray-9">
                        {{ __("Ticket details") }}
                      </p>
                      <div class="space-y-3 text-base">
                        <div class="flex items-center justify-between">
                          <span class="text-ink-gray-6">{{
                            __("Status")
                          }}</span>
                          <span
                            class="flex items-center gap-1.5 text-ink-gray-8"
                          >
                            <svg
                              :class="[
                                replied ? 'text-ink-blue-6' : 'text-ink-red-6',
                                'size-4',
                              ]"
                              viewBox="0 0 16 16"
                            >
                              <circle
                                cx="8"
                                cy="8"
                                r="3.5"
                                fill="currentColor"
                              />
                            </svg>
                            {{ replied ? __("Awaiting Response") : __("Open") }}
                          </span>
                        </div>
                        <div class="flex items-center justify-between">
                          <span class="text-ink-gray-6">{{
                            __("Ticket")
                          }}</span>
                          <span class="tabular-nums text-ink-gray-8">
                            #{{ SAMPLE_TICKET.id }}
                          </span>
                        </div>
                        <div class="flex items-center justify-between">
                          <span class="text-ink-gray-6">{{
                            __("Priority")
                          }}</span>
                          <span class="text-ink-gray-8">{{
                            __("Medium")
                          }}</span>
                        </div>
                        <div class="flex items-center justify-between">
                          <span class="text-ink-gray-6">{{
                            __("Opened")
                          }}</span>
                          <span class="text-ink-gray-8">{{
                            __("Today, 10:42")
                          }}</span>
                        </div>
                      </div>
                    </aside>
                  </div>
                </Transition>
              </div>
            </Transition>
          </div>
        </div>

        <div
          v-if="!reducedMotion"
          class="pointer-events-none absolute left-0 top-0 z-10 transition-transform duration-700 ease-[cubic-bezier(.65,0,.35,1)]"
          :style="{ transform: `translate(${cursor.x}px, ${cursor.y}px)` }"
        >
          <span
            ref="ripple"
            class="absolute -left-4 -top-4 size-8 rounded-full bg-surface-gray-9 opacity-0"
          />
          <div ref="cursorEl" class="origin-top-left">
            <svg class="size-5 drop-shadow-md" viewBox="0 0 20 20" fill="none">
              <path
                d="M3 2 L3 16 L7 12.5 L9.6 18 L12 17 L9.5 11.6 L15 11.4 Z"
                fill="#111"
                stroke="#fff"
                stroke-width="1.4"
                stroke-linejoin="round"
              />
            </svg>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useAuthStore } from "@/stores/auth";
import { __ } from "@/translation";
import { useElementSize } from "@vueuse/core";
import HDLogo from "@/assets/logos/HDLogo.vue";
import { Avatar, Button } from "frappe-ui";
import { computed, onBeforeUnmount, reactive, ref, watch } from "vue";
import SetupPreviewDesk from "./SetupPreviewDesk.vue";
import { SAMPLE_TICKET, avatarUrl, nameOf } from "./preview";
import { brand, invitees, setup } from "./setup";

const FRAPPE_LOGO = "/assets/frappe/images/frappe-framework-logo.svg";

type Page = "login" | "home" | "desk-list" | "desk-ticket" | "portal-ticket";
type Point = { x: number; y: number };

const TRAFFIC_LIGHTS = ["bg-[#ff5f57]", "bg-[#febc2e]", "bg-[#28c840]"];
const W = 1120;
const H = 720;
const SITE = window.location.host;
const authStore = useAuthStore();

const stage = ref<HTMLElement | null>(null);
const { width, height } = useElementSize(stage);
const scale = computed(
  () => Math.min(1.15, (width.value * 0.92) / 0.75 / W) || 0.9
);
const box = computed(() => ({
  left: width.value * 0.08,
  top: Math.max(84, height.value * 0.14),
  width: W * scale.value,
  height: H * scale.value,
}));

const agent = computed(() => invitees.value[0]);
const replied = computed(() => !!agent.value?.sent);
const arrived = computed(() => setup.ticketArrived);

const target = computed<Page>(() => {
  if (setup.showDone) return arrived.value ? "portal-ticket" : "home";
  if (setup.step === "password") return "login";
  if (setup.step === "workspace") return "home";
  if (setup.step === "email") return "desk-list";
  return arrived.value ? "desk-ticket" : "desk-list";
});
const isPortalPage = (p: Page) => p === "home" || p === "portal-ticket";

const reducedMotion = !!window.matchMedia?.("(prefers-reduced-motion: reduce)")
  .matches;
const page = ref<Page>(target.value);
const TAB_POINTS: Record<"desk" | "portal", Point> = {
  desk: { x: 204, y: 26 },
  portal: { x: 448, y: 26 },
};
const REST: Record<Page, Point> = {
  login: { x: 560, y: 468 },
  home: { x: 600, y: 346 },
  "desk-list": { x: 780, y: 430 },
  "desk-ticket": { x: 300, y: 470 },
  "portal-ticket": { x: 640, y: 600 },
};
const rest = (p: Page) =>
  p === "desk-ticket" && agent.value && !replied.value
    ? { x: 448, y: 690 }
    : REST[p];

function clickPoint(from: Page, to: Page): Point | null {
  if (from === "desk-list" && to === "desk-ticket") return { x: 420, y: 250 };
  if (from === "desk-ticket" && to === "desk-list") return { x: 96, y: 109 };
  if (isPortalPage(from) !== isPortalPage(to))
    return isPortalPage(to) ? TAB_POINTS.portal : TAB_POINTS.desk;
  return null;
}

const cursor = reactive({ ...rest(page.value) });
const cursorEl = ref<HTMLElement | null>(null);
const ripple = ref<HTMLElement | null>(null);
function click() {
  cursorEl.value?.animate(
    [
      { transform: "scale(1)" },
      { transform: "scale(.82)" },
      { transform: "scale(1)" },
    ],
    { duration: 260, easing: "ease-out" }
  );
  ripple.value?.animate(
    [
      { transform: "scale(.3)", opacity: 0.5 },
      { transform: "scale(1.8)", opacity: 0 },
    ],
    { duration: 600, easing: "ease-out" }
  );
}

let timers: number[] = [];
const later = (ms: number, fn: () => void) =>
  timers.push(window.setTimeout(fn, ms));
watch(target, (to) => {
  timers.forEach(clearTimeout);
  timers = [];
  const point = clickPoint(page.value, to);
  if (reducedMotion || !point) {
    page.value = to;
    Object.assign(cursor, rest(to));
    return;
  }
  Object.assign(cursor, point);
  later(800, () => {
    click();
    page.value = to;
    later(650, () => Object.assign(cursor, rest(to)));
  });
});
watch(replied, (r) => {
  if (!r || page.value !== "desk-ticket") return;
  click();
  later(700, () => Object.assign(cursor, REST["desk-ticket"]));
});
watch(agent, () => {
  if (page.value === "desk-ticket") Object.assign(cursor, rest("desk-ticket"));
});
onBeforeUnmount(() => timers.forEach(clearTimeout));

const isPortal = computed(() => isPortalPage(page.value));
const isDesk = computed(
  () => page.value === "desk-list" || page.value === "desk-ticket"
);
const slide = computed(() => ({
  enterActiveClass:
    "transition duration-500 delay-100 ease-[cubic-bezier(.22,1,.36,1)] motion-reduce:transition-none",
  enterFromClass: isPortal.value
    ? "opacity-0 translate-x-8"
    : "opacity-0 -translate-x-8",
  leaveActiveClass:
    "absolute inset-0 transition duration-150 ease-in motion-reduce:transition-none",
  leaveToClass: "opacity-0",
}));

const PATHS: Record<Page, string> = {
  login: "/login",
  home: "/help",
  "portal-ticket": `/help/tickets/${SAMPLE_TICKET.id}`,
  "desk-list": "/helpdesk/tickets",
  "desk-ticket": `/helpdesk/tickets/${SAMPLE_TICKET.id}`,
};
const url = computed(() => SITE + PATHS[page.value]);
const tabs = computed(() => [
  {
    key: "desk",
    desk: true,
    active: !isPortal.value,
    title:
      page.value === "login"
        ? __("Login")
        : page.value === "desk-ticket"
        ? SAMPLE_TICKET.subject
        : __("Tickets"),
  },
  { key: "portal", desk: false, active: isPortal.value, title: brand.value },
]);

const passwordDots = computed(() => Math.min(setup.password.length, 22));

const CATEGORIES = [
  {
    icon: "lucide-user-round",
    title: __("Account and login"),
    description: __("Passwords, two-factor and profile settings."),
  },
  {
    icon: "lucide-receipt",
    title: __("Billing"),
    description: __("Invoices, payment methods and refunds."),
  },
  {
    icon: "lucide-rocket",
    title: __("Getting started"),
    description: __("Set up your workspace in a few minutes."),
  },
];

const fade = {
  mode: "out-in" as const,
  enterActiveClass:
    "transition duration-300 ease-out motion-reduce:transition-none",
  enterFromClass: "opacity-0",
  leaveActiveClass: "transition duration-150 motion-reduce:transition-none",
  leaveToClass: "opacity-0",
};
</script>
