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
        <span>{{ __("Name") }}</span>
        <span>{{ __("Role") }}</span>
        <span v-if="showLastSeen" class="max-sm:hidden">{{
          __("Last seen")
        }}</span>
        <span />
      </div>

      <div
        v-for="member in matches"
        :key="keyOf(member)"
        :class="[ROW, 'min-h-13']"
      >
        <div class="flex min-w-0 items-center gap-2">
          <Avatar
            class="has-[>div:first-child]:border has-[>div:first-child]:border-outline-gray-2"
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
            </div>
            <div class="truncate text-p-sm text-ink-gray-5">
              {{ member.email }}
            </div>
          </div>
        </div>

        <div>
          <Dropdown
            v-if="canEditRole(member)"
            :options="roleOptions(member)"
            align="start"
          >
            <template #trigger>
              <button
                type="button"
                class="flex cursor-pointer items-center gap-1 text-base text-ink-gray-8 hover:text-ink-gray-9"
              >
                {{ roleLabel(member.role) }}
                <LucideChevronDown class="size-3.5 text-ink-gray-5" />
              </button>
            </template>
          </Dropdown>
          <span v-else class="text-base text-ink-gray-8">{{
            roleLabel(member.role)
          }}</span>
        </div>

        <div v-if="showLastSeen" class="text-p-sm text-ink-gray-5 max-sm:hidden">
          {{ lastSeen(member) }}
        </div>

        <div class="flex justify-end">
          <Dropdown
            v-if="canRemove(member)"
            :options="removeOptions(member)"
            align="end"
          >
            <template #trigger="{ open }">
              <Button
                variant="ghost"
                icon="lucide-more-horizontal"
                :aria-label="__('Member actions')"
                :active="open"
              />
            </template>
          </Dropdown>
        </div>
      </div>

      <div
        v-for="invite in matchingInvites"
        :key="invite.invitation"
        :class="[ROW, 'min-h-13']"
      >
        <div class="flex min-w-0 items-center gap-2">
          <div
            class="flex size-7 shrink-0 items-center justify-center rounded-full border border-dashed border-outline-gray-3"
          >
            <LucideMail class="size-3.5 text-ink-gray-5" />
          </div>
          <div class="min-w-0">
            <div class="truncate text-base-medium text-ink-gray-8">
              {{ invite.email }}
            </div>
            <div class="truncate text-p-sm text-ink-gray-5">
              {{ invitedLabel(invite) }}
            </div>
          </div>
        </div>

        <span class="text-base text-ink-gray-5">{{
          roleLabel(invite.role)
        }}</span>

        <div v-if="showLastSeen" class="text-p-sm text-ink-gray-5 max-sm:hidden">
          {{ __("Pending") }}
        </div>

        <div class="flex justify-end">
          <Tooltip :text="__('Cancel invitation')">
            <Button
              variant="ghost"
              icon="lucide-x"
              :aria-label="__('Cancel invitation')"
              @click="emit('cancel', invite)"
            />
          </Tooltip>
        </div>
      </div>

      <div
        v-if="!matches.length && !matchingInvites.length"
        class="py-6 text-center text-p-sm text-ink-gray-5"
      >
        {{ __("No members match this filter.") }}
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";
import {
  Avatar,
  Button,
  Dropdown,
  Select,
  TextInput,
  Tooltip,
} from "frappe-ui";
import LucideChevronDown from "~icons/lucide/chevron-down";
import LucideMail from "~icons/lucide/mail";
import LucideSearch from "~icons/lucide/search";
import LucideUsers from "~icons/lucide/users";
import { __ } from "@helpdesk/shared/translation";
import { timeAgo } from "@helpdesk/shared/utils";
import {
  ASSIGNABLE_ROLES,
  ROLES,
  roleLabel,
  type RoleLabel,
} from "@app/stores/settings/roles";
import { matchesQuery } from "@app/utils";

// A phone drops "Last seen", so the name keeps its width; only managers get it at all.
const ROW = computed(() =>
  props.showLastSeen
    ? "grid grid-cols-[minmax(0,1fr)_104px_32px] sm:grid-cols-[minmax(0,1fr)_104px_120px_32px] items-center gap-3 py-2"
    : "grid grid-cols-[minmax(0,1fr)_104px_32px] items-center gap-3 py-2"
);

type Member = {
  contact?: string;
  full_name: string;
  email?: string;
  image?: string;
  last_seen?: string;
  role: RoleLabel;
  is_you?: boolean;
};

type Invite = {
  invitation: string;
  email: string;
  role: RoleLabel;
  invited_by?: string;
  invited_by_you?: boolean;
  invited_on?: string;
};

// Owner is left out: there is one per organization, already first in the list.
const roleFilters = computed(() => [
  { label: __("All"), value: "All", icon: LucideUsers },
  ...ASSIGNABLE_ROLES.map((role) => ({
    label: roleLabel(role),
    value: role,
    icon: ROLES[role].icon,
  })),
  ...(props.invites.length
    ? [{ label: __("Invited"), value: "Invited", icon: LucideMail }]
    : []),
]);

const props = withDefaults(
  defineProps<{
    members?: Member[];
    invites?: Invite[];
    canChangeRoles?: boolean;
    canRemoveMembers?: boolean;
    showLastSeen?: boolean;
  }>(),
  {
    members: () => [],
    invites: () => [],
    canChangeRoles: false,
    canRemoveMembers: false,
  }
);

const emit = defineEmits<{
  setRole: [member: Member, role: RoleLabel];
  remove: [member: Member];
  cancel: [invite: Invite];
}>();

const role = ref("All");
const search = ref("");

const matches = computed(() =>
  props.members.filter((member) => matchesRole(member) && matchesSearch(member))
);

const matchingInvites = computed(() =>
  ["All", "Invited"].includes(role.value)
    ? props.invites.filter((invite) => matchesQuery(search.value, invite.email))
    : []
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

function invitedLabel(invite: Invite) {
  const when = timeAgo(invite.invited_on);
  return invite.invited_by_you
    ? __("Invited {0} by you", [when])
    : __("Invited {0} by {1}", [when, invite.invited_by]);
}

// The owner's role is fixed, and changing yourself revokes the rights the call needs.
function canEditRole(member: Member) {
  return props.canChangeRoles && member.role !== "Owner" && !member.is_you;
}

function canRemove(member: Member) {
  return props.canRemoveMembers && member.role !== "Owner" && !member.is_you;
}

function roleOptions(member: Member) {
  return ASSIGNABLE_ROLES.map((role) => ({
    label: roleLabel(role),
    selected: member.role === role,
    onClick: () => member.role !== role && emit("setRole", member, role),
  }));
}

function removeOptions(member: Member) {
  return [
    {
      label: __("Remove from organization"),
      icon: "lucide-user-minus",
      onClick: () => emit("remove", member),
    },
  ];
}

function keyOf(member: Member) {
  return member.contact || member.email;
}
</script>
