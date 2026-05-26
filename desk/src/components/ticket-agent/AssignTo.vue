<template>
  <Popover
    class="flex w-full"
    placement="bottom-end"
    :matchTargetWidth="true"
    v-model:show="popoverIsOpen"
  >
    <template #target="{ togglePopover }">
      <div class="flex flex-col gap-1.5 w-full">
        <span v-if="!hideLabel" class="block text-xs text-ink-gray-5">{{
          __("Assignee")
        }}</span>
        <Button
          ref="triggerRef"
          variant="outline"
          class="!flex !justify-start w-full active:!bg-inherit hover:shadow-sm [&>span]:w-full"
          @click="togglePopover()"
        >
          <div class="flex items-center min-h-[20px] gap-2 w-full">
            <template v-if="localAssignees.length > 0">
              <MultipleAvatar
                :avatars="localAssignees.map((a) => a.name)"
                size="sm"
              />
              <span
                v-if="localAssignees.length > 1"
                class="text-ink-gray-7 truncate"
              >
                {{ localAssignees.length }} {{ __("assignees") }}
              </span>
            </template>
            <template v-else>
              <span class="text-ink-gray-5">{{ __("No one") }}</span>
              <span
                v-if="!popoverIsOpen"
                class="text-xs text-ink-gray-6 hover:text-ink-gray-8 cursor-pointer underline ml-auto"
                @click.stop="assignSelf"
              >
                {{ __("Assign yourself") }}
              </span>
            </template>
          </div>
          <template #suffix>
            <LucideChevronDown class="h-4 w-4 ml-auto text-ink-gray-5" />
          </template>
        </Button>
      </div>
    </template>
    <template #body="{ isOpen }">
      <div
        v-if="isOpen"
        class="my-2 divide-y divide-outline-gray-modals rounded-lg bg-surface-modal shadow-2xl ring-1 ring-black ring-opacity-5 focus:outline-none"
        @keydown.ctrl.enter.capture.stop="confirmAssignment"
        @keydown.meta.enter.capture.stop="confirmAssignment"
        @keydown.esc.capture.stop="cancelAssignment"
      >
        <!-- Search Header -->
        <div class="p-1">
          <div
            class="flex h-7 items-center text-sm font-medium text-ink-gray-6 justify-between"
          >
            <input
              ref="inputRef"
              v-model="searchText"
              :placeholder="__('Search agents...')"
              class="px-2 flex-1 bg-transparent border-none outline-none text-sm focus:border-none focus:ring-0 text-ink-gray-6 placeholder-ink-gray-4"
              @click.stop
              @keydown="handleInputKeydown"
            />
            <Button
              v-if="searchText.length > 0"
              variant="ghost"
              size="sm"
              @click="searchText = ''"
            >
              <template #icon>
                <LucideX class="size-4" />
              </template>
            </Button>
          </div>
        </div>

        <!-- Availability filters -->
        <div class="flex items-center gap-1.5 px-2 py-1.5 overflow-x-auto">
          <button
            v-for="filter in availabilityFilters"
            :key="filter.value"
            class="flex items-center gap-1.5 rounded-full px-2 py-1 text-xs font-medium whitespace-nowrap"
            :class="
              availabilityFilter === filter.value
                ? 'bg-surface-gray-3 text-ink-gray-9'
                : 'text-ink-gray-6 hover:bg-surface-gray-2'
            "
            @click="availabilityFilter = filter.value"
          >
            <p
              v-if="filter.dotClass"
              class="size-1.5 rounded-full text-p-sm"
              :class="filter.dotClass"
            />
            {{ filter.label }}

            <span class="text-xs text-ink-gray-5">{{ filter.count }}</span>
          </button>
        </div>

        <!-- Agent List -->
        <div class="px-1.5 pb-1.5 max-h-64 overflow-y-auto">
          <div class="pt-1.5">
            <!-- Loading state -->
            <div
              v-if="agentResource.loading"
              class="px-2 py-4 text-center text-sm text-ink-gray-5"
            >
              {{ __("Loading...") }}
            </div>

            <template v-else-if="sortedAgentOptions.length > 0">
              <button
                v-for="(agent, index) in sortedAgentOptions"
                :key="agent.value"
                :ref="(el) => setOptionRef(index, el as Element)"
                class="group flex w-full items-center rounded px-2 py-1.5 text-base text-ink-gray-6 gap-2"
                :class="
                  index === highlightedIndex
                    ? 'bg-surface-gray-3'
                    : 'hover:bg-surface-gray-3'
                "
                @click="toggleAgent(agent)"
              >
                <Checkbox
                  :modelValue="isSelected(agent.value)"
                  class="flex-shrink-0"
                />
                <div class="relative flex-shrink-0">
                  <UserAvatar :name="agent.value" size="sm" />
                  <div
                    class="absolute bottom-0 -right-0.5 size-2 rounded-full outline outline-white outline-1.5"
                    :class="statusColor(agent.availability || '')"
                  />
                </div>
                <div class="flex flex-col flex-1 text-left min-w-0">
                  <span class="text-ink-gray-7 truncate text-p-sm">
                    {{ agent.label }}
                  </span>
                  <span
                    v-if="
                      availabilitySubtitle(
                        agent.availability,
                        agent.availability_changed_on
                      )
                    "
                    class="text-xs text-ink-gray-5 truncate"
                  >
                    {{
                      availabilitySubtitle(
                        agent.availability,
                        agent.availability_changed_on
                      )
                    }}
                  </span>
                </div>
              </button>
            </template>

            <!-- No results -->
            <div v-else class="px-2 py-4 text-center text-sm text-ink-gray-5">
              {{ __("No agents found") }}
            </div>
          </div>
        </div>

        <!-- Footer -->
        <div class="flex items-center justify-end px-2 py-1.5 gap-2">
          <Button variant="outline" size="sm" @click="cancelAssignment">
            {{ __("Cancel") }}
          </Button>
          <Button variant="solid" size="sm" @click="confirmAssignment">
            {{
              isMobileView
                ? __("Assign")
                : isMac
                ? __("Assign (⌘ + ⏎)")
                : __("Assign (Ctrl + ⏎)")
            }}
          </Button>
        </div>
      </div>
    </template>
  </Popover>
</template>

<script setup lang="ts">
import { statusColor, useAvailability } from "@/composables/useAvailability";
import { useDevice } from "@/composables";
import { useScreenSize } from "@/composables/screen";
import { useShortcut } from "@/composables/shortcuts";
import { useUserStore } from "@/stores/user";
import { capture } from "@/telemetry";
import { __ } from "@/translation";
import { prettyDate } from "@/utils";
import {
  ActivitiesSymbol,
  AgentOption,
  AssigneeSymbol,
  TicketSymbol,
} from "@/types";
import { useDebounceFn } from "@vueuse/core";
import {
  Button,
  Checkbox,
  Popover,
  call,
  createListResource,
  createResource,
  toast,
} from "frappe-ui";
import { computed, inject, nextTick, ref, useTemplateRef, watch } from "vue";

import LucideSearch from "~icons/lucide/search";
import MultipleAvatar from "../MultipleAvatar.vue";
import UserAvatar from "../UserAvatar.vue";
import { HDAgent } from "@/types/doctypes";

interface Props {
  hideLabel?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  hideLabel: false,
});

const { hideLabel } = props;
const { isMac } = useDevice();
const { isMobileView } = useScreenSize();

const ticket = inject(TicketSymbol)!;
const assignees = inject(AssigneeSymbol)!;
const activities = inject(ActivitiesSymbol)!;

const { getUser } = useUserStore();
const { currentStatus } = useAvailability();
const currentUser = computed(() => getUser("")); // empty string returns current user
const currentAgentName = (window as any).agent as string | null;

const searchText = ref("");
const highlightedIndex = ref(0);
const inputRef = useTemplateRef<HTMLInputElement>("inputRef");
const triggerRef = useTemplateRef("triggerRef");

const popoverIsOpen = ref(false);
const hasBeenOpened = ref(false);

// Local copy of assignees
const localAssignees = ref<{ name: string; image: string; label: string }[]>(
  []
);
const snapshotAssignees = ref<{ name: string; image: string; label: string }[]>(
  []
);

// Sync from injected assignees when popover is not open
watch(
  () => assignees.value?.data,
  (data) => {
    if (!popoverIsOpen.value && data) {
      localAssignees.value = [...data];
    }
  },
  { immediate: true, deep: true }
);

// Track whether the next close was triggered by Assign (commit) vs Cancel/outside-click (revert).
const justConfirmed = ref(false);

watch(popoverIsOpen, (isOpen) => {
  if (isOpen) {
    hasBeenOpened.value = true;
    snapshotAssignees.value = localAssignees.value.map((a) => ({ ...a }));
    pinnedSelectedNames.value = new Set(
      localAssignees.value.map((a) => a.name)
    );
    searchText.value = "";
    highlightedIndex.value = 0;
    availabilityFilter.value = "All";
    nextTick(() => {
      inputRef.value?.focus();
    });
    return;
  }

  if (!hasBeenOpened.value) return;
  hasBeenOpened.value = false;
  searchText.value = "";

  if (justConfirmed.value) {
    justConfirmed.value = false;
    const currentNames = localAssignees.value.map((a) => a.name);
    const oldNames = snapshotAssignees.value.map((a) => a.name);
    const added = currentNames.filter((n) => !oldNames.includes(n));
    const removed = oldNames.filter((n) => !currentNames.includes(n));
    saveAssignees(added, removed);
  } else {
    // Cancel / click-outside → revert to snapshot
    localAssignees.value = snapshotAssignees.value.map((a) => ({ ...a }));
  }
});

function cancelAssignment() {
  popoverIsOpen.value = false;
}

function confirmAssignment() {
  justConfirmed.value = true;
  popoverIsOpen.value = false;
}

function availabilitySubtitle(
  availability?: string,
  changedOn?: string
): string {
  if (availability === "Active") return __("Active now");
  if (availability !== "Busy" && availability !== "Away") return "";

  const label = availability === "Busy" ? __("Busy") : __("Away");
  const elapsed = changedOn
    ? prettyDate(changedOn, true)?.toLocaleLowerCase()
    : "";
  return elapsed ? `${label} · ${elapsed}` : label;
}

const agentResource = createListResource({
  doctype: "HD Agent",
  fields: [
    "name",
    "agent_name",
    "user_image",
    "availability",
    "availability_changed_on",
  ],
  filters: { is_active: true },
  pageLength: 20,
  auto: true,
});

// Fetch current agent separately to guarantee they appear in the list
const currentAgentResource = currentAgentName
  ? createResource({
      url: "frappe.client.get",
      params: {
        doctype: "HD Agent",
        name: currentAgentName,
        fields: [
          "name",
          "agent_name",
          "user_image",
          "availability",
          "availability_changed_on",
        ],
      },
      auto: true,
    })
  : null;

const debouncedSearch = useDebounceFn((text: string) => {
  const filters: Record<string, any> = { is_active: true };
  if (text) {
    filters.agent_name = ["like", `%${text}%`];
  }
  agentResource.filters = filters;
  agentResource.reload();
}, 300);

watch(searchText, (text) => {
  debouncedSearch(text);
});

type AvailabilityFilter = "All" | "Active" | "Busy" | "Away";
const availabilityFilter = ref<AvailabilityFilter>("All");

const availabilityFilters = computed(() => {
  const counts = { Active: 0, Busy: 0, Away: 0 };
  for (const opt of agentOptions.value) {
    const v = opt.availability;
    if (v === "Active" || v === "Busy" || v === "Away") counts[v]++;
  }
  const total = agentOptions.value.length;
  return [
    { value: "All" as const, label: __("All"), count: total, dotClass: "" },
    {
      value: "Active" as const,
      label: __("Active"),
      count: counts.Active,
      dotClass: statusColor("Active"),
    },
    {
      value: "Busy" as const,
      label: __("Busy"),
      count: counts.Busy,
      dotClass: statusColor("Busy"),
    },
    {
      value: "Away" as const,
      label: __("Away"),
      count: counts.Away,
      dotClass: statusColor("Away"),
    },
  ];
});

const agentOptions = computed<AgentOption[]>(() => {
  const agents: AgentOption[] = [];
  const options = new Set<string>();

  // Include current agent only when not searching
  if (!searchText.value && currentAgentResource?.data) {
    const a = currentAgentResource.data;
    agents.push({
      value: a.name,
      label: a.agent_name || getUser(a.name).full_name,
      image: a.user_image || getUser(a.name).user_image,
      availability: currentStatus.value || a.availability,
      availability_changed_on: a.availability_changed_on,
    });
    options.add(a.name);
  }

  if (agentResource.data) {
    for (const agent of agentResource.data) {
      if (!options.has(agent.name)) {
        agents.push({
          value: agent.name,
          label: agent.agent_name || getUser(agent.name).full_name,
          image: agent.user_image || getUser(agent.name).user_image,
          availability: agent.availability,
          availability_changed_on: agent.availability_changed_on,
        });
        options.add(agent.name);
      }
    }
  }

  return agents;
});

// Snapshot of selected names at open time — used to pin assigned agents at top
// without them jumping around as the user toggles selections.
const pinnedSelectedNames = ref<Set<string>>(new Set());

const sortedAgentOptions = computed<AgentOption[]>(() => {
  const options = [...agentOptions.value];
  const isSearching = searchText.value.length > 0;

  // Merge in any locally-selected agents not present in the fetched list
  // (e.g. agents found via search who aren't in the default top 20)
  const seen = new Set(options.map((o) => o.value));
  if (!isSearching) {
    for (const a of localAssignees.value) {
      if (!seen.has(a.name)) {
<<<<<<< HEAD
        options.push({ value: a.name, label: a.label, image: a.image });
=======
        const user = getUser(a.name);
        options.push({
          value: a.name,
          label: a.label || user.full_name || a.name,
          image: a.image || user.user_image,
          availability: a.availability,
        });
>>>>>>> a9268b86 (feat: handle manual assignment for away agents)
        seen.add(a.name);
      }
    }
  }

  const pinned = pinnedSelectedNames.value;

  const selfOption: AgentOption[] = [];
  const assigned: AgentOption[] = [];
  const rest: AgentOption[] = [];

  for (const opt of options) {
    if (!isSearching && currentAgentName && opt.value === currentAgentName) {
      selfOption.push(opt);
    } else if (pinned.has(opt.value)) {
      assigned.push(opt);
    } else {
      rest.push(opt);
    }
  }

  // If there are pinned assignees, show them first then current user, otherwise current user first
<<<<<<< HEAD
  if (assigned.length > 0) {
    return [...assigned, ...selfOption, ...rest];
  }
  return [...selfOption, ...rest];
=======
  const ordered =
    assigned.length > 0
      ? [...assigned, ...selfOption, ...rest]
      : [...selfOption, ...rest];

  if (availabilityFilter.value === "All") return ordered;
  return ordered.filter((opt) => opt.availability === availabilityFilter.value);
>>>>>>> 9d970c51 (feat: calculate and display time from agent status change)
});

function isSelected(agentName: string): boolean {
  return localAssignees.value.some((a) => a.name === agentName);
}

function toggleAgent(agent: AgentOption) {
  const isSearching = searchText.value.length > 0;
  if (isSelected(agent.value)) {
    localAssignees.value = localAssignees.value.filter(
      (a) => a.name !== agent.value
    );
    // Only unpin if it was pinned during search, keep original pins stable
    if (isSearching) {
      pinnedSelectedNames.value.delete(agent.value);
    }
  } else {
    localAssignees.value.push({
      name: agent.value,
      image: agent.image || "",
      label: agent.label,
    });
    // Pin only when selecting during search so they stay visible when search clears
    if (isSearching) {
      pinnedSelectedNames.value.add(agent.value);
    }
  }
}

// Keyboard navigation, ref forwarding to scroll highlighted option into view
const optionRefs = ref<Map<number, Element>>(new Map());

function setOptionRef(index: number, el: Element | null) {
  if (el) {
    optionRefs.value.set(index, el);
  } else {
    optionRefs.value.delete(index);
  }
}

// Only scroll when highlightedIndex changes (keyboard nav), not on every re-render
watch(highlightedIndex, (index) => {
  nextTick(() => {
    optionRefs.value.get(index)?.scrollIntoView({ block: "nearest" });
  });
});

function handleInputKeydown(event: KeyboardEvent) {
  if (
    event.key === "Enter" &&
    sortedAgentOptions.value[highlightedIndex.value]
  ) {
    event.preventDefault();
    event.stopPropagation();
    toggleAgent(sortedAgentOptions.value[highlightedIndex.value]);
  } else if (event.key === "ArrowDown") {
    event.preventDefault();
    highlightedIndex.value = Math.min(
      highlightedIndex.value + 1,
      sortedAgentOptions.value.length - 1
    );
  } else if (event.key === "ArrowUp") {
    event.preventDefault();
    highlightedIndex.value = Math.max(highlightedIndex.value - 1, 0);
  }
}

// Reset highlight when search changes
watch(searchText, () => {
  highlightedIndex.value = 0;
});

async function logActivity(action: string) {
  await call("frappe.client.insert", {
    doc: {
      doctype: "HD Ticket Activity",
      ticket: ticket.value?.name,
      action,
    },
  });
}

async function assignSelf() {
  if (!currentAgentName) return;

  if (localAssignees.value.some((a) => a.name === currentAgentName)) return;

  const self = currentUser.value;
  localAssignees.value.push({
    name: currentAgentName,
    image: self.user_image || "",
    label: self.full_name,
  });

  try {
    await addAssigneesResource.submit([currentAgentName]);
    await logActivity(`assigned ${currentAgentName}`);
    capture("ticket_assigned", { doctype: "HD Ticket" });
    toast.success(__("Assignee's updated successfully."));
    assignees.value.reload();
    activities.value.reload();
  } catch {
    toast.error(__("Failed to update Assignee's."));
    localAssignees.value = localAssignees.value.filter(
      (a) => a.name !== currentAgentName
    );
  }
}

// triggered when the popover is closed
const addAssigneesResource = createResource({
  url: "frappe.desk.form.assign_to.add",
  makeParams: (addedAssignees: string[]) => ({
    doctype: "HD Ticket",
    name: ticket.value?.name,
    assign_to: addedAssignees,
  }),
  onSuccess: () => {
    capture("ticket_assigned", { doctype: "HD Ticket" });
  },
});

const removeAssigneesResource = createResource({
  url: "helpdesk.api.doc.remove_assignments",
  makeParams: (removedAssignees: string[]) => ({
    doctype: "HD Ticket",
    name: ticket.value?.name,
    assignees: removedAssignees,
  }),
});

async function saveAssignees(added: string[], removed: string[]) {
  if (!added.length && !removed.length) return;

  try {
    if (removed.length) {
      const removeResult = await removeAssigneesResource.submit(removed);
      if (removeResult?.exc) throw new Error(removeResult.exc);
    }
    if (added.length) {
      const unavailableAgents = (agentResource.data as HDAgent[])?.filter(
        (agent) =>
          added.includes(agent.name) &&
          (agent.availability === "Away" || agent.availability === "Busy")
      );
      if (unavailableAgents?.length > 0) {
        for (const agent of unavailableAgents) {
          const name = agent.agent_name || agent.name;
          const message =
            agent.availability === "Busy"
              ? __("{0} is currently busy", [name])
              : __("{0} is currently away", [name]);
          toast.warning(message);
        }
      }

      const addResult = await addAssigneesResource.submit(added);
      if (addResult?.exc) throw new Error(addResult.exc);
    }

    // Log activity only after API calls succeed
    const logParts: string[] = [];
    if (added.length) logParts.push(`assigned ${added.join(", ")}`);
    if (removed.length) logParts.push(`unassigned ${removed.join(", ")}`);
    await logActivity(logParts.join(" & "));

    toast.success(__("Assignees updated successfully."));
    assignees.value.reload();
    activities.value.reload();
  } catch {
    toast.error(__("Failed to update Assignees."));
    localAssignees.value = [...snapshotAssignees.value];
  }
}

useShortcut("a", () => {
  (triggerRef.value?.$el as HTMLElement)?.click();
});
</script>
