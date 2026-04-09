<template>
  <Popover
    class="flex w-full"
    placement="bottom-end"
    :matchTargetWidth="true"
    v-model:show="popoverIsOpen"
  >
    <template #target="{ togglePopover }">
      <div class="flex flex-col gap-1.5 w-full">
        <span class="block text-xs text-gray-600">{{ __("Assignee") }}</span>
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
      >
        <!-- Search Header -->
        <div class="py-1.5 px-1.5">
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
                class="group flex h-7 w-full items-center rounded px-2 text-base text-ink-gray-6 gap-2"
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
                <UserAvatar :name="agent.value" size="sm" class="" />
                <span class="text-ink-gray-7 flex-1 text-left truncate">
                  {{ agent.label }}
                </span>
              </button>
            </template>

            <!-- No results -->
            <div v-else class="px-2 py-4 text-center text-sm text-ink-gray-5">
              {{ __("No agents found") }}
            </div>
          </div>
        </div>
      </div>
    </template>
  </Popover>
</template>

<script setup lang="ts">
import { useShortcut } from "@/composables/shortcuts";
import { useUserStore } from "@/stores/user";
import { capture } from "@/telemetry";
import { __ } from "@/translation";
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
import MultipleAvatar from "../MultipleAvatar.vue";
import UserAvatar from "../UserAvatar.vue";

const ticket = inject(TicketSymbol)!;
const assignees = inject(AssigneeSymbol)!;
const activities = inject(ActivitiesSymbol)!;

const { getUser } = useUserStore();
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

// Watch popover open/close — same pattern as old AssignToBody
watch(popoverIsOpen, (isOpen) => {
  if (isOpen) {
    // Opening: take snapshot
    hasBeenOpened.value = true;
    snapshotAssignees.value = localAssignees.value.map((a) => ({ ...a }));
    pinnedSelectedNames.value = new Set(
      localAssignees.value.map((a) => a.name)
    );
    searchText.value = "";
    highlightedIndex.value = 0;
    nextTick(() => {
      inputRef.value?.focus();
    });
  } else if (hasBeenOpened.value) {
    // Closing after a real open: compute diff and save
    hasBeenOpened.value = false;
    searchText.value = "";
    const currentNames = localAssignees.value.map((a) => a.name);
    const oldNames = snapshotAssignees.value.map((a) => a.name);
    const added = currentNames.filter((n) => !oldNames.includes(n));
    const removed = oldNames.filter((n) => !currentNames.includes(n));
    saveAssignees(added, removed);
  }
});

const agentResource = createListResource({
  doctype: "HD Agent",
  fields: ["name", "agent_name", "user_image"],
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
        fields: ["name", "agent_name", "user_image"],
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
        options.push({ value: a.name, label: a.label, image: a.image });
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
  if (assigned.length > 0) {
    return [...assigned, ...selfOption, ...rest];
  }
  return [...selfOption, ...rest];
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
  (triggerRef.value?.$el as HTMLElement)?.nextElementSibling?.click();
});
</script>
