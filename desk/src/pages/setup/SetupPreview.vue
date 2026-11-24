<template>
  <div class="relative h-full w-full bg-surface-gray-1">
    <div class="absolute start-20 top-0 flex h-20 items-center">
      <Transition v-bind="fade">
        <span :key="String(isPortal)" class="text-base text-ink-gray-6">
          {{
            isPortal ? __("What your customers see") : __("What your team sees")
          }}
        </span>
      </Transition>
    </div>

    <SetupPreviewFrame
      ref="frame"
      :url="url"
      :tabs="tabs"
      :user="{ name: authStore.userName, image: authStore.userImage }"
      :cursor="cursor"
    >
      <template #tab-icon>
        <img
          v-if="setup.brandLogo"
          :src="setup.brandLogo"
          alt=""
          class="size-full object-cover dark:bg-white"
        />
        <HDLogo v-else class="size-full" />
      </template>
      <Transition v-bind="slide">
        <SetupPreviewLogin
          v-if="page === 'login'"
          key="login"
          :email="authStore.userId"
          :password-length="setup.passwordLength"
          :ready="setup.passwordReady"
          :email-link="false"
          :labels="loginLabels"
        >
          <template #logo>
            <img
              v-if="setup.brandLogo"
              :src="setup.brandLogo"
              alt=""
              class="rounded-[7px] object-cover dark:bg-white"
            />
            <HDLogo v-else />
          </template>
        </SetupPreviewLogin>

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
            <span class="text-lg-medium text-ink-gray-9">{{ brand }}</span>
            <div class="ms-auto flex items-center gap-5 text-base">
              <span class="text-ink-gray-7">{{ __("Knowledge base") }}</span>
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
                      __("Explore answers to frequently asked questions about")
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
              <div class="mx-auto flex max-w-[832px] flex-col gap-5 px-4 pt-8">
                <div class="flex min-h-7 items-center justify-between gap-4">
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
                  <span class="text-ink-gray-5">{{ __("My tickets") }}</span>
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
                    <span class="lucide-paperclip size-4 text-ink-gray-5" />
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
                    <span class="text-ink-gray-6">{{ __("Status") }}</span>
                    <span class="flex items-center gap-1.5 text-ink-gray-8">
                      <svg
                        :class="[
                          replied ? 'text-ink-blue-6' : 'text-ink-red-6',
                          'size-4',
                        ]"
                        viewBox="0 0 16 16"
                      >
                        <circle cx="8" cy="8" r="3.5" fill="currentColor" />
                      </svg>
                      {{ replied ? __("Awaiting Response") : __("Open") }}
                    </span>
                  </div>
                  <div class="flex items-center justify-between">
                    <span class="text-ink-gray-6">{{ __("Ticket") }}</span>
                    <span class="tabular-nums text-ink-gray-8">
                      #{{ SAMPLE_TICKET.id }}
                    </span>
                  </div>
                  <div class="flex items-center justify-between">
                    <span class="text-ink-gray-6">{{ __("Priority") }}</span>
                    <span class="text-ink-gray-8">{{ __("Medium") }}</span>
                  </div>
                  <div class="flex items-center justify-between">
                    <span class="text-ink-gray-6">{{ __("Opened") }}</span>
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
    </SetupPreviewFrame>
  </div>
</template>

<script setup lang="ts">
import { useAuthStore } from "@/stores/auth";
import { __ } from "@/translation";
import { SetupPreviewFrame, SetupPreviewLogin } from "@framework/ui";
import { usePreferredReducedMotion } from "@vueuse/core";
import HDLogo from "@/assets/logos/HDLogo.vue";
import { Button } from "frappe-ui";
import { computed, onBeforeUnmount, ref, watch } from "vue";
import SetupPreviewDesk from "./SetupPreviewDesk.vue";
import { SAMPLE_TICKET, nameOf } from "./preview";
import { useSetupFlow } from "./setup";

const { brand, invitees, setup } = useSetupFlow();

type Page = "login" | "home" | "desk-list" | "desk-ticket" | "portal-ticket";
type Point = { x: number; y: number };

const SITE = window.location.host;
const authStore = useAuthStore();

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

const motion = usePreferredReducedMotion();
const reducedMotion = computed(() => motion.value === "reduce");
const page = ref<Page>(target.value);
// Where the pointer rests on each page and where it clicks to move on, in the app's pixels
// below the browser bar; the tabs sit in the bar, above the app.
const TAB_POINTS: Record<"desk" | "portal", Point> = {
  desk: { x: 204, y: -62 },
  portal: { x: 448, y: -62 },
};
const REST: Record<Page, Point | string> = {
  login: '[data-slot="setup-preview-login-submit"]',
  home: { x: 600, y: 258 },
  "desk-list": { x: 780, y: 342 },
  "desk-ticket": { x: 300, y: 382 },
  "portal-ticket": { x: 640, y: 512 },
};
const rest = (p: Page) =>
  p === "desk-ticket" && agent.value && !replied.value
    ? { x: 448, y: 602 }
    : REST[p];

function clickPoint(from: Page, to: Page): Point | null {
  if (from === "desk-list" && to === "desk-ticket") return { x: 420, y: 162 };
  if (from === "desk-ticket" && to === "desk-list") return { x: 96, y: 21 };
  if (isPortalPage(from) !== isPortalPage(to))
    return isPortalPage(to) ? TAB_POINTS.portal : TAB_POINTS.desk;
  return null;
}

const frame = ref<InstanceType<typeof SetupPreviewFrame> | null>(null);
const cursor = ref<Point | string>(rest(page.value));
const click = () => frame.value?.click();

let timers: number[] = [];
const later = (ms: number, fn: () => void) =>
  timers.push(window.setTimeout(fn, ms));
watch(target, (to) => {
  timers.forEach(clearTimeout);
  timers = [];
  const point = clickPoint(page.value, to);
  if (reducedMotion.value || !point) {
    page.value = to;
    cursor.value = rest(to);
    return;
  }
  cursor.value = point;
  later(800, () => {
    click();
    page.value = to;
    later(650, () => (cursor.value = rest(to)));
  });
});
watch(replied, (r) => {
  if (!r || page.value !== "desk-ticket") return;
  click();
  later(700, () => (cursor.value = REST["desk-ticket"]));
});
watch(agent, () => {
  if (page.value === "desk-ticket") cursor.value = rest("desk-ticket");
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
    active: !isPortal.value,
    title:
      page.value === "login"
        ? __("Login")
        : page.value === "desk-ticket"
        ? SAMPLE_TICKET.subject
        : __("Tickets"),
  },
  // Keyed, so the company name changes in place as the owner types it.
  { key: "portal", active: isPortal.value, title: brand.value },
]);

const loginLabels = {
  title: __("Sign In"),
  subtitle: __("Welcome! Please sign in to continue."),
  email: __("Email"),
  password: __("Password"),
  forgot: __("Forgot password?"),
  submit: __("Continue"),
};

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
