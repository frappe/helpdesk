<template>
  <div>
    <div class="mb-3 flex items-center gap-2">
      <TextInput
        v-model="search"
        type="text"
        :placeholder="__('Search')"
        class="min-w-0 flex-1"
      >
        <template #prefix>
          <LucideSearch class="size-4 text-ink-gray-5" />
        </template>
      </TextInput>
      <Select v-model="role" :options="roleFilters" size="sm" />
    </div>

    <div>
      <div :class="[ROW, 'min-h-8 pt-0 text-p-xs text-ink-gray-5']">
        <span>{{ __("Members") }}</span>
        <span class="max-sm:hidden">{{ __("Last seen") }}</span>
        <span>{{ __("Role") }}</span>
        <span />
      </div>

      <div
        v-for="member in matches"
        :key="keyOf(member)"
        :class="[ROW, 'min-h-13']"
      >
        <div class="flex min-w-0 items-center gap-2">
          <Avatar
            shape="circle"
            size="lg"
            :image="member.image"
            :label="member.full_name"
          />
          <div class="min-w-0">
            <div
              class="flex items-center gap-1.5 truncate text-base-medium text-ink-gray-8"
            >
              {{ member.full_name }}
              <span
                v-if="member.is_you"
                class="text-p-xs font-normal text-ink-gray-5"
                >{{ __("You") }}</span
              >
              <Badge
                v-if="member.pending"
                :label="__('Pending')"
                theme="amber"
                variant="subtle"
              />
            </div>
            <div
              v-if="!member.pending"
              class="truncate text-p-sm text-ink-gray-5"
            >
              {{ member.email }}
            </div>
          </div>
        </div>

        <div class="text-p-sm text-ink-gray-5 max-sm:hidden">
          {{ lastSeen(member) }}
        </div>

        <span
          class="inline-flex items-center gap-1.5 text-p-base text-ink-gray-7"
        >
          <component :is="ROLES[member.role].icon" class="size-4" />
          {{ roleLabel(member.role) }}
        </span>

        <div class="flex justify-end">
          <Dropdown
            v-if="canRemove(member)"
            :options="rowOptions(member)"
            align="end"
          >
            <template #trigger="{ open }">
              <Button
                variant="ghost"
                icon="lucide-more-horizontal"
                :active="open"
              />
            </template>
          </Dropdown>
        </div>
      </div>

      <div
        v-if="!matches.length"
        class="py-6 text-center text-p-sm text-ink-gray-5"
      >
        {{ __("No members match this filter.") }}
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";
import { Avatar, Badge, Button, Dropdown, Select, TextInput } from "frappe-ui";
import LucideSearch from "~icons/lucide/search";
import LucideUsers from "~icons/lucide/users";
import { __ } from "@helpdesk/shared/translation";
import { timeAgo } from "@helpdesk/shared/utils";
import { ROLES, roleLabel, type RoleLabel } from "@app/stores/settings/roles";
import { matchesQuery } from "@app/utils";

// A phone drops "Last seen", so the name keeps its width.
const ROW =
  "grid grid-cols-[minmax(0,1fr)_auto_32px] sm:grid-cols-[minmax(0,1fr)_120px_132px_32px] items-center gap-3 border-b border-outline-gray-1 py-2 last:border-b-0";

type Member = {
  contact?: string;
  invitation?: string;
  full_name: string;
  email?: string;
  image?: string;
  last_seen?: string;
  role: RoleLabel;
  is_you?: boolean;
  pending?: boolean;
};

// Owner is left out: there is one per organization, already first in the list.
const FILTERABLE_ROLES: RoleLabel[] = ["Manager", "Member"];
const roleFilters = computed(() => [
  { label: __("All"), value: "All", icon: LucideUsers },
  ...FILTERABLE_ROLES.map((role) => ({
    label: roleLabel(role),
    value: role,
    icon: ROLES[role].icon,
  })),
]);

const props = withDefaults(
  defineProps<{
    members?: Member[];
    canManage?: boolean;
  }>(),
  { members: () => [], canManage: false }
);

const emit = defineEmits<{
  setRole: [member: Member, role: RoleLabel];
  remove: [member: Member];
}>();

const role = ref("All");
const search = ref("");

const matches = computed(() =>
  props.members.filter((member) => matchesRole(member) && matchesSearch(member))
);

function matchesRole(member: Member) {
  return role.value === "All" || member.role === role.value;
}

function matchesSearch(member: Member) {
  return matchesQuery(search.value, member.full_name, member.email);
}

function lastSeen(member: Member) {
  return member.last_seen ? timeAgo(member.last_seen) : __("Never");
}

// The owner's role is fixed, and demoting yourself revokes the rights the call needs.
function canSwitchRole(member: Member) {
  return Boolean(
    props.canManage &&
      member.role !== "Owner" &&
      !member.is_you &&
      !member.pending
  );
}

function canRemove(member: Member) {
  return Boolean(props.canManage && member.role !== "Owner" && !member.is_you);
}

function rowOptions(member: Member) {
  if (member.pending) {
    return [
      {
        label: __("Cancel invitation"),
        icon: "lucide-x-circle",
        onClick: () => emit("remove", member),
      },
    ];
  }
  const next: RoleLabel = member.role === "Manager" ? "Member" : "Manager";
  return [
    {
      label: next === "Manager" ? __("Make manager") : __("Make member"),
      icon: ROLES[next].icon,
      onClick: () => emit("setRole", member, next),
      condition: () => canSwitchRole(member),
    },
    {
      label: __("Remove from organization"),
      icon: "lucide-user-minus",
      onClick: () => emit("remove", member),
    },
  ];
}

function keyOf(member: Member) {
  return member.contact || member.invitation || member.email;
}
</script>
