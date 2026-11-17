<template>
  <div
    class="flex h-full transition-[width] duration-500 ease-[cubic-bezier(.22,1,.36,1)]"
    :class="rail ? 'w-[840px]' : 'w-full'"
  >
    <Sidebar
      width="15rem"
      :collapsed="rail"
      class="shrink-0 border-r border-outline-gray-1"
    >
      <div class="flex h-full flex-col p-2">
        <div
          class="flex h-12 w-full items-center rounded-5 py-2"
          :class="rail ? 'justify-center' : 'px-2'"
        >
          <span
            class="flex size-8 shrink-0 items-center justify-center overflow-hidden rounded-[7px] bg-surface-gray-9 text-base-semibold text-ink-gray-1"
          >
            <img
              v-if="setup.brandLogo"
              :src="setup.brandLogo"
              alt=""
              class="size-full object-cover"
            />
            <template v-else>{{ brand[0] }}</template>
          </span>
          <template v-if="!rail">
            <div class="ms-2 flex min-w-0 flex-1 flex-col pe-2">
              <span
                class="truncate text-base-medium leading-none text-ink-gray-9"
              >
                {{ brand }}
              </span>
              <span class="mt-1 truncate text-sm text-ink-gray-7">
                {{ authStore.userName }}
              </span>
            </div>
            <span class="lucide-chevron-down size-4 text-ink-gray-5" />
          </template>
        </div>

        <nav class="mt-2 flex flex-col gap-0.5">
          <SidebarItem :label="__('Search')">
            <template #prefix>
              <span class="lucide-search size-4 text-ink-gray-7" />
            </template>
            <template #suffix>
              <span class="me-2 text-sm text-ink-gray-5">⌘K</span>
            </template>
          </SidebarItem>
          <SidebarItem :label="__('Notifications')">
            <template #prefix>
              <span class="lucide-bell size-4 text-ink-gray-7" />
            </template>
          </SidebarItem>
          <SidebarItem
            v-for="(n, i) in NAV"
            :key="n.label"
            :label="n.label"
            :active="n.tickets"
            :class="i === 0 && 'mt-4'"
          >
            <template #prefix>
              <span :class="[n.icon, 'size-4 text-ink-gray-7']" />
            </template>
          </SidebarItem>
        </nav>

        <div class="mt-auto flex flex-col gap-2">
          <Button
            v-if="rail"
            class="mx-auto"
            icon="lucide-list-checks"
            tabindex="-1"
          />
          <div
            v-else
            class="mx-2 flex flex-col gap-3 rounded-6 bg-surface-elevation-2 px-3 py-2.5 text-base shadow-sm"
          >
            <div class="inline-flex gap-2 text-ink-gray-9">
              <span class="lucide-list-checks my-0.5 size-4 shrink-0" />
              <div class="flex flex-col gap-0.5 text-p-sm">
                <span class="font-medium">{{ __("Getting started") }}</span>
                <Transition
                  mode="out-in"
                  enter-active-class="transition duration-300"
                  enter-from-class="opacity-0"
                >
                  <span :key="done" class="text-ink-gray-7">
                    {{ __("{0}/10 steps", [done]) }}
                  </span>
                </Transition>
              </div>
            </div>
            <Button
              :label="done ? __('Continue') : __('Start now')"
              theme="blue"
              icon-left="lucide-chevrons-right"
              tabindex="-1"
            />
          </div>
          <SidebarItem :label="__('Help')">
            <template #prefix>
              <span class="lucide-circle-help size-4 text-ink-gray-7" />
            </template>
          </SidebarItem>
          <SidebarItem :label="__('Collapse')">
            <template #prefix>
              <span class="lucide-panel-left size-4 text-ink-gray-7" />
            </template>
          </SidebarItem>
        </div>
      </div>
    </Sidebar>

    <div class="relative flex min-w-0 flex-1 flex-col overflow-hidden">
      <Transition
        enter-active-class="transition duration-500 delay-100 ease-[cubic-bezier(.22,1,.36,1)] motion-reduce:transition-none"
        :enter-from-class="
          page === 'desk-ticket'
            ? 'opacity-0 translate-x-6'
            : 'opacity-0 -translate-x-6'
        "
        leave-active-class="absolute inset-0 transition duration-150 ease-in motion-reduce:transition-none"
        leave-to-class="opacity-0"
      >
        <div
          v-if="page === 'desk-list'"
          key="list"
          class="flex h-full flex-col"
        >
          <header
            class="flex h-[42px] shrink-0 items-center justify-between border-b border-outline-gray-1 px-5"
          >
            <div class="flex items-center gap-1 text-lg">
              <span class="text-ink-gray-5">{{ __("Tickets") }}</span>
              <span class="text-ink-gray-4">/</span>
              <span class="lucide-list ms-1 size-4 text-ink-gray-7" />
              <span class="text-ink-gray-9">{{ __("List") }}</span>
              <span class="lucide-chevron-down ms-1 size-4 text-ink-gray-6" />
            </div>
            <Button
              variant="solid"
              theme="gray"
              icon-left="lucide-plus"
              :label="__('Create')"
              tabindex="-1"
            />
          </header>

          <div class="flex items-center gap-2 px-5 py-4">
            <span
              v-for="q in [__('ID'), __('Subject')]"
              :key="q"
              class="flex h-7 w-36 items-center rounded-4 bg-surface-gray-2 px-2 text-base text-ink-gray-4"
            >
              {{ q }}
            </span>
            <span
              v-for="q in [__('Customer'), __('Source')]"
              :key="q"
              class="flex h-7 w-36 items-center justify-between rounded-4 bg-surface-gray-2 px-2 text-base text-ink-gray-4"
            >
              {{ q }}<span class="lucide-chevron-down size-4 text-ink-gray-5" />
            </span>
            <div
              class="ms-auto flex items-center gap-2 border-l border-outline-gray-2 ps-2"
            >
              <Button icon="lucide-refresh-cw" tabindex="-1" />
              <Button
                :label="__('Filter')"
                icon-left="lucide-list-filter"
                tabindex="-1"
              />
              <Button
                :label="__('Sort')"
                icon-left="lucide-arrow-down-up"
                tabindex="-1"
              />
              <Button icon="lucide-columns-3" tabindex="-1" />
            </div>
          </div>

          <div class="min-h-0 flex-1 px-5">
            <List
              :columns="COLUMNS"
              :row-height="40"
              selectable
              class="[--list-row-padding-x:0.75rem]"
            >
              <ListHeader class="rounded-4 bg-surface-gray-2">
                <ListHeaderCell>{{ __("ID") }}</ListHeaderCell>
                <ListHeaderCell>{{ __("Subject") }}</ListHeaderCell>
                <ListHeaderCell>{{ __("Status") }}</ListHeaderCell>
                <ListHeaderCell>{{ __("Assigned To") }}</ListHeaderCell>
                <ListHeaderCell>{{ __("First Response") }}</ListHeaderCell>
                <ListHeaderCell>{{ __("Priority") }}</ListHeaderCell>
                <ListHeaderCell>{{ __("Created") }}</ListHeaderCell>
              </ListHeader>
              <TransitionGroup v-bind="fade">
                <div v-for="r in rows" :key="r.id">
                  <ListRows :items="[r]" v-slot="{ item, value }">
                    <ListRow
                      :value="value"
                      class="transition-colors duration-[1500ms]"
                      :class="item.fresh && !replied && 'bg-surface-gray-2'"
                    >
                      <ListCell>
                        <span class="text-base tabular-nums text-ink-gray-6">
                          {{ item.id }}
                        </span>
                      </ListCell>
                      <ListCell>
                        <span
                          class="truncate text-base text-ink-gray-9"
                          :class="item.unseen && 'font-semibold'"
                        >
                          {{ item.subject }}
                        </span>
                      </ListCell>
                      <ListCell>
                        <span
                          class="flex items-center gap-1.5 text-base text-ink-gray-8"
                        >
                          <StatusDot :class="STATUS_COLOR[item.status]" />
                          {{ item.status }}
                        </span>
                      </ListCell>
                      <ListCell>
                        <Transition
                          mode="out-in"
                          enter-active-class="transition duration-500"
                          enter-from-class="opacity-0 scale-75"
                        >
                          <span
                            v-if="item.assigned"
                            :key="item.assigned"
                            class="flex min-w-0 items-center gap-1.5 text-base text-ink-gray-8"
                          >
                            <Avatar
                              :label="item.assigned"
                              :image="avatarUrl(item.assigned)"
                              size="sm"
                            />
                            <span class="truncate">{{
                              nameOf(item.assigned)
                            }}</span>
                          </span>
                        </Transition>
                      </ListCell>
                      <ListCell>
                        <Badge
                          :label="item.response"
                          :theme="responseTheme(item.response)"
                          variant="subtle"
                        />
                      </ListCell>
                      <ListCell>
                        <span
                          class="flex items-center gap-2 text-base text-ink-gray-8"
                        >
                          <svg
                            v-if="item.priority === 'Urgent'"
                            class="size-3.5"
                            viewBox="0 0 14 14"
                            fill="none"
                          >
                            <rect
                              width="14"
                              height="14"
                              rx="4"
                              class="fill-ink-gray-6"
                            />
                            <rect
                              x="6.25"
                              y="3"
                              width="1.5"
                              height="4.75"
                              rx="0.75"
                              class="fill-surface-gray-1"
                            />
                            <circle
                              cx="7"
                              cy="10"
                              r="0.9"
                              class="fill-surface-gray-1"
                            />
                          </svg>
                          <PriorityBars
                            v-else
                            :faded="FADED_BARS[item.priority] ?? 0"
                          />
                          {{ item.priority }}
                        </span>
                      </ListCell>
                      <ListCell>
                        <span class="text-base text-ink-gray-6">{{
                          item.created
                        }}</span>
                      </ListCell>
                    </ListRow>
                  </ListRows>
                </div>
              </TransitionGroup>
            </List>
          </div>

          <footer
            class="flex h-12 shrink-0 items-center justify-between border-t border-outline-gray-1 px-5"
          >
            <div class="flex rounded-4 bg-surface-gray-2 p-0.5 text-sm">
              <span
                class="rounded-[6px] bg-surface-base px-2 py-1 text-ink-gray-9 shadow-sm"
              >
                20
              </span>
              <span class="px-2 py-1 text-ink-gray-6">50</span>
              <span class="px-2 py-1 text-ink-gray-6">100</span>
            </div>
            <span class="text-base tabular-nums text-ink-gray-5">
              {{ __("{0} of {0}", [rows.length]) }}
            </span>
          </footer>
        </div>

        <div v-else key="ticket" class="flex h-full flex-col">
          <header
            class="flex h-[42px] shrink-0 items-center justify-between border-b border-outline-gray-1 px-5"
          >
            <div class="flex min-w-0 items-center gap-1 text-lg">
              <span class="text-ink-gray-5">{{ __("Tickets") }}</span>
              <span class="text-ink-gray-4">/</span>
              <span class="truncate text-ink-gray-9">{{
                SAMPLE_TICKET.subject
              }}</span>
            </div>
            <div class="flex items-center gap-2">
              <Button
                :label="replied ? __('Replied') : __('Open')"
                tabindex="-1"
              >
                <template #prefix>
                  <StatusDot
                    :class="replied ? 'text-ink-blue-6' : 'text-ink-red-6'"
                  />
                </template>
              </Button>
              <Button icon="lucide-ellipsis" tabindex="-1" />
            </div>
          </header>

          <div class="flex min-h-0 flex-1">
            <div class="flex min-w-0 flex-1 flex-col">
              <div class="flex gap-6 border-b border-outline-gray-1 px-5">
                <span
                  v-for="(t, i) in TABS"
                  :key="t.label"
                  class="-mb-px flex items-center gap-1.5 border-b py-3 text-base"
                  :class="
                    i === 0
                      ? 'border-outline-gray-9 text-ink-gray-9'
                      : 'border-transparent text-ink-gray-6'
                  "
                >
                  <span :class="[t.icon, 'size-4']" />{{ t.label }}
                </span>
              </div>

              <div class="min-h-0 flex-1 space-y-5 overflow-hidden p-5">
                <PreviewMessage
                  :author="SAMPLE_TICKET.customer"
                  :avatar="SAMPLE_TICKET.customer"
                  :when="__('2 minutes ago')"
                  :paragraphs="SAMPLE_TICKET.message"
                />
                <Transition v-bind="fade">
                  <PreviewMessage
                    v-if="replied && agent"
                    :author="nameOf(agent.email)"
                    :avatar="agent.email"
                    :when="__('just now')"
                    :paragraphs="SAMPLE_TICKET.reply"
                  />
                </Transition>
              </div>

              <div class="border-t border-outline-gray-1">
                <div class="flex gap-1.5 px-5 py-2.5">
                  <Button
                    variant="ghost"
                    :label="__('Reply')"
                    icon-left="lucide-mail"
                    tabindex="-1"
                    :class="!replied && agent && '!bg-surface-gray-4'"
                  />
                  <Button
                    variant="ghost"
                    :label="__('Comment')"
                    icon-left="lucide-message-square"
                    tabindex="-1"
                  />
                </div>
                <div v-if="!replied && agent">
                  <div
                    class="mx-5 flex items-center gap-2 border-y border-outline-gray-1 py-2.5"
                  >
                    <span class="text-p-xs text-ink-gray-4"
                      >{{ __("To") }}:</span
                    >
                    <Button
                      size="sm"
                      :label="SAMPLE_TICKET.email"
                      tabindex="-1"
                    />
                    <div class="ms-auto flex gap-1.5">
                      <Button
                        variant="ghost"
                        :label="__('Cc')"
                        class="!text-ink-gray-4"
                        tabindex="-1"
                      />
                      <Button
                        variant="ghost"
                        :label="__('Bcc')"
                        class="!text-ink-gray-4"
                        tabindex="-1"
                      />
                    </div>
                  </div>
                  <p class="mx-5 min-h-16 py-3 text-p-sm text-ink-gray-4">
                    {{ SAMPLE_TICKET.draft }}
                  </p>
                  <div
                    class="flex items-center justify-between gap-2 border-t border-outline-gray-1 px-4 py-2.5"
                  >
                    <div class="flex items-center gap-1.5 p-1 text-ink-gray-8">
                      <span
                        v-for="icon in COMPOSER_ICONS"
                        :key="icon"
                        class="flex rounded-4 p-1"
                      >
                        <span :class="icon" class="size-4" />
                      </span>
                    </div>
                    <div class="flex min-w-0 items-center gap-2">
                      <span class="truncate text-sm text-ink-gray-5">
                        {{
                          __("{0} replies once invited", [nameOf(agent.email)])
                        }}
                      </span>
                      <Button :label="__('Discard')" tabindex="-1" />
                      <Button
                        variant="solid"
                        :label="__('Send (⌘ + ⏎)')"
                        disabled
                        tabindex="-1"
                      />
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <aside
              class="flex w-[320px] shrink-0 flex-col border-l border-outline-gray-1"
            >
              <div class="space-y-4 p-4">
                <div class="flex items-center gap-3">
                  <Avatar
                    :label="SAMPLE_TICKET.customer"
                    :image="avatarUrl(SAMPLE_TICKET.customer)"
                    size="3xl"
                  />
                  <div class="min-w-0">
                    <p class="truncate text-lg-medium text-ink-gray-9">
                      {{ SAMPLE_TICKET.customer }}
                    </p>
                    <p class="text-sm text-ink-gray-6">
                      {{ __("#{0} via Email", [SAMPLE_TICKET.id]) }}
                    </p>
                  </div>
                </div>
                <div class="space-y-0.5">
                  <div class="flex min-h-7 items-center gap-2 text-base">
                    <span class="w-[106px] shrink-0 text-ink-gray-6">
                      {{ __("First Response") }}
                    </span>
                    <span
                      class="ps-[9px] transition-colors"
                      :class="replied ? 'text-ink-green-6' : 'text-ink-gray-8'"
                    >
                      {{ replied ? __("Fulfilled") : __("Due in 1h 58m") }}
                    </span>
                  </div>
                  <div class="flex min-h-7 items-center gap-2 text-base">
                    <span class="w-[106px] shrink-0 text-ink-gray-6">
                      {{ __("Resolution") }}
                    </span>
                    <span class="ps-[9px] text-ink-gray-8">{{
                      __("Due in 23h 58m")
                    }}</span>
                  </div>
                </div>
              </div>
              <div class="border-t border-outline-gray-1">
                <p
                  class="flex items-center gap-1 px-4 pb-2 pt-3 text-base-medium text-ink-gray-9"
                >
                  {{ __("Overview") }}
                  <span class="lucide-chevron-down size-4 text-ink-gray-6" />
                </p>
                <div class="space-y-2.5 px-4 pb-4 text-base">
                  <div class="flex min-h-7 items-center gap-2">
                    <span class="w-[106px] shrink-0 text-ink-gray-6">
                      {{ __("Assignee") }}
                    </span>
                    <Transition
                      mode="out-in"
                      enter-active-class="transition duration-300"
                      enter-from-class="opacity-0"
                    >
                      <span
                        v-if="agent"
                        :key="agent.email"
                        class="flex min-w-0 items-center gap-1.5 ps-[9px] text-ink-gray-8"
                      >
                        <Avatar
                          :label="agent.email"
                          :image="avatarUrl(agent.email)"
                          size="xs"
                        />
                        <span class="truncate">{{ nameOf(agent.email) }}</span>
                      </span>
                      <span
                        v-else
                        class="flex flex-1 items-center justify-between ps-[9px] text-ink-gray-4"
                      >
                        {{ __("Set Assignee...") }}
                        <span class="lucide-chevron-down size-4" />
                      </span>
                    </Transition>
                  </div>
                  <div class="flex min-h-7 items-center gap-2">
                    <span class="w-[106px] shrink-0 text-ink-gray-6">
                      {{ __("Priority") }}
                    </span>
                    <span
                      class="flex items-center gap-2 ps-[9px] text-ink-gray-8"
                    >
                      <PriorityBars :faded="1" />{{ __("Medium") }}
                    </span>
                  </div>
                  <div
                    v-for="f in [__('Ticket Type'), __('Customer'), __('Team')]"
                    :key="f"
                    class="flex min-h-7 items-center gap-2"
                  >
                    <span class="w-[106px] shrink-0 text-ink-gray-6">{{
                      f
                    }}</span>
                    <span
                      class="flex flex-1 items-center justify-between ps-[9px] text-ink-gray-4"
                    >
                      {{ __("Set {0}...", [f]) }}
                      <span class="lucide-chevron-down size-4" />
                    </span>
                  </div>
                  <div class="flex min-h-7 items-center gap-2">
                    <span class="w-[106px] shrink-0 text-ink-gray-6">{{
                      __("Tags")
                    }}</span>
                    <span class="ps-[9px] text-ink-gray-7">{{
                      __("+ Add")
                    }}</span>
                  </div>
                </div>
              </div>
              <p
                class="flex items-center gap-1 border-t border-outline-gray-1 px-4 py-3 text-base-medium text-ink-gray-9"
              >
                {{ __("Recent Tickets") }}
                <span class="lucide-chevron-right size-4 text-ink-gray-6" />
              </p>
            </aside>
          </div>
        </div>
      </Transition>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useAuthStore } from "@/stores/auth";
import { __ } from "@/translation";
import { Avatar, Badge, Button, Sidebar, SidebarItem } from "frappe-ui";
import {
  List,
  ListCell,
  ListHeader,
  ListHeaderCell,
  ListRow,
  ListRows,
} from "frappe-ui/list";
import { computed, defineComponent, h } from "vue";
import { SAMPLE_TICKET, avatarUrl, nameOf } from "./preview";
import { brand, invitees, setup } from "./setup";

const props = defineProps<{ page: "desk-list" | "desk-ticket" }>();
const rail = computed(() => props.page === "desk-ticket");
const authStore = useAuthStore();

const agent = computed(() => invitees.value[0]);
const replied = computed(() => !!agent.value?.sent);
const done = computed(
  () => Number(!!setup.mailbox) + Number(invitees.value.some((a) => a.sent))
);

const NAV = [
  { icon: "lucide-house", label: __("Home") },
  { icon: "lucide-layout-dashboard", label: __("Dashboard") },
  { icon: "lucide-ticket", label: __("Tickets"), tickets: true },
  { icon: "lucide-book-open", label: __("Knowledge Base") },
  { icon: "lucide-building-2", label: __("Customers") },
  { icon: "lucide-users", label: __("Contacts") },
];
const STATUS_COLOR: Record<string, string> = {
  Open: "text-ink-red-6",
  Replied: "text-ink-blue-6",
  Resolved: "text-ink-green-6",
  Closed: "text-ink-gray-5",
};
const FADED_BARS: Record<string, number> = { High: 0, Medium: 1, Low: 2 };
const COLUMNS = [
  "3.5rem",
  "15rem",
  "7rem",
  "8rem",
  "7.5rem",
  "6.5rem",
  "4.5rem",
];
const TABS = [
  { label: __("Activity"), icon: "lucide-activity" },
  { label: __("Emails"), icon: "lucide-mail" },
  { label: __("Comments"), icon: "lucide-message-square" },
  { label: __("Analytics"), icon: "lucide-chart-no-axes-column" },
];

const row = (
  id: string,
  subject: string,
  status: string,
  response: string,
  assigned: string,
  priority: string,
  created: string,
  unseen = false
) => ({
  id,
  subject,
  status,
  response,
  assigned,
  priority,
  created,
  unseen,
  fresh: false,
});
const SAMPLE_ROWS = [
  row(
    "1041",
    __("Invoice shows the wrong billing address"),
    "Replied",
    "Fulfilled",
    "sam@example.com",
    "High",
    "25m"
  ),
  row(
    "1040",
    __("Can't export reports to CSV"),
    "Open",
    "in 1h",
    "maya@example.com",
    "Urgent",
    "1h",
    true
  ),
  row(
    "1039",
    __("How do I add a second admin?"),
    "Replied",
    "Fulfilled",
    "priya@example.com",
    "Low",
    "3h"
  ),
  row(
    "1038",
    __("Webhook retries keep failing"),
    "Open",
    "Failed",
    "leo@example.com",
    "High",
    "5h"
  ),
  row(
    "1037",
    __("Request: dark mode for the portal"),
    "Resolved",
    "Fulfilled",
    "priya@example.com",
    "Low",
    "1d"
  ),
  row(
    "1036",
    __("SSO login loops back to the sign-in page"),
    "Open",
    "in 3h",
    "leo@example.com",
    "Medium",
    "1d",
    true
  ),
  row(
    "1035",
    __("Refund for a duplicate charge"),
    "Resolved",
    "Fulfilled",
    "sam@example.com",
    "Medium",
    "2d"
  ),
  row(
    "1034",
    __("Attachments over 10 MB fail to upload"),
    "Closed",
    "Fulfilled",
    "leo@example.com",
    "Medium",
    "3d"
  ),
];
const rows = computed(() => {
  if (!setup.ticket) return SAMPLE_ROWS;
  const fresh = {
    ...row(
      SAMPLE_TICKET.id,
      SAMPLE_TICKET.subject,
      replied.value ? "Replied" : "Open",
      replied.value ? "Fulfilled" : "in 2h",
      agent.value?.email ?? authStore.userId,
      "Medium",
      "now",
      true
    ),
    fresh: true,
  };
  return [fresh, ...SAMPLE_ROWS];
});
const responseTheme = (response: string) =>
  response === "Fulfilled" ? "gray" : response === "Failed" ? "red" : "amber";

const StatusDot = () =>
  h(
    "svg",
    { class: "size-4 shrink-0 transition-colors", viewBox: "0 0 16 16" },
    [h("circle", { cx: 8, cy: 8, r: 3.5, fill: "currentColor" })]
  );

const BARS = [
  { x: 0, y: 8, h: 4 },
  { x: 4, y: 4, h: 8 },
  { x: 8, y: 0, h: 12 },
];
const PriorityBars = (props: { faded: number }) =>
  h(
    "svg",
    { class: "size-3", viewBox: "0 0 10 12", fill: "none" },
    BARS.map((bar, n) =>
      h("rect", {
        x: bar.x,
        y: bar.y,
        width: 2.5,
        height: bar.h,
        rx: 0.5,
        class: 2 - n < props.faded ? "fill-ink-gray-3" : "fill-ink-gray-6",
      })
    )
  );
PriorityBars.props = ["faded"];

const PreviewMessage = defineComponent({
  props: { author: String, avatar: String, when: String, paragraphs: Array },
  setup(props) {
    const actions = ["lucide-reply", "lucide-reply-all", "lucide-ellipsis"];
    return () =>
      h("div", { class: "flex gap-3" }, [
        h(Avatar, {
          label: props.author,
          image: avatarUrl(props.avatar as string),
          size: "md",
          class: "mt-2",
        }),
        h(
          "div",
          { class: "min-w-0 flex-1 rounded-4 border border-outline-gray-2" },
          [
            h("div", { class: "flex h-10 items-center gap-2 px-3" }, [
              h(
                "span",
                { class: "text-base-medium text-ink-gray-9" },
                props.author
              ),
              h(
                "span",
                { class: "ms-auto text-sm text-ink-gray-5" },
                props.when
              ),
              ...actions.map((icon) =>
                h("span", { class: `${icon} size-4 text-ink-gray-6` })
              ),
            ]),
            h(
              "div",
              {
                class:
                  "space-y-2 border-t border-outline-gray-2 px-3 py-3 text-p-base text-ink-gray-8",
              },
              (props.paragraphs as string[]).map((p) => h("p", p))
            ),
          ]
        ),
      ]);
  },
});

const fade = {
  enterActiveClass:
    "transition duration-700 ease-[cubic-bezier(.22,1,.36,1)] motion-reduce:transition-none",
  enterFromClass: "opacity-0 -translate-y-3",
  moveClass:
    "transition-transform duration-700 ease-[cubic-bezier(.22,1,.36,1)]",
};
const COMPOSER_ICONS = ["lucide-paperclip", "lucide-zap"];
</script>
