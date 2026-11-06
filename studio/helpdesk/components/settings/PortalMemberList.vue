<template>
  <div class="flex min-h-0 flex-col">
    <div class="mb-3 flex shrink-0 items-center gap-2">
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

    <div :class="[ROW, 'min-h-8 shrink-0 text-p-xs text-ink-gray-5']">
      <span>{{ __("Name") }}</span>
      <span>{{ __("Role") }}</span>
      <span v-if="showLastActive" class="max-sm:hidden">{{
        __("Last seen")
      }}</span>
      <span />
    </div>

    <div v-if="loading" class="min-h-0 flex-1 overflow-hidden" aria-busy="true">
      <span class="sr-only" role="status">{{ __("Loading") }}</span>
      <div v-for="i in 5" :key="i" :class="[ROW, BODY_ROW]">
        <div class="flex min-w-0 items-center gap-2">
          <Skeleton :class="[BLOCK, 'size-8 shrink-0 rounded-full']" />
          <!-- Name-over-email height, so rows don't jump. -->
          <div
            class="flex h-[39px] min-w-0 flex-1 flex-col justify-center gap-2"
          >
            <Skeleton
              :class="[BLOCK, 'h-2.5 rounded-full']"
              :style="{ width: `${30 + ((i * 17) % 25)}%` }"
            />
            <Skeleton
              :class="[BLOCK, 'h-2 rounded-full']"
              :style="{ width: `${45 + ((i * 13) % 25)}%` }"
            />
          </div>
        </div>
        <Skeleton :class="[BLOCK, 'h-2.5 w-14 rounded-full']" />
        <Skeleton
          v-if="showLastActive"
          :class="[BLOCK, 'h-2 w-16 rounded-full max-sm:hidden']"
        />
        <span />
      </div>
    </div>

    <div v-else class="portal-reveal min-h-0 flex-1 overflow-y-auto">
      <div
        v-for="member in matches"
        :key="keyOf(member)"
        :class="[ROW, BODY_ROW]"
      >
        <div class="flex min-w-0 items-center gap-2">
          <Avatar
            shape="circle"
            size="lg"
            :image="member.image"
            :label="member.full_name"
          />
          <div class="min-w-0">
            <div class="truncate text-base-medium text-ink-gray-8">
              {{ member.full_name }}
            </div>
            <div class="truncate text-p-sm text-ink-gray-5">
              {{ member.email }}
            </div>
          </div>
        </div>

        <span class="text-base text-ink-gray-8">{{
          roleLabel(member.role)
        }}</span>

        <div
          v-if="showLastActive"
          class="text-p-sm text-ink-gray-5 max-sm:hidden"
        >
          {{ lastActive(member) }}
        </div>

        <div :class="ACTIONS">
          <Dropdown
            v-if="canManage(member)"
            :options="memberOptions(member)"
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
        v-for="invitation in matchingInvitations"
        :key="invitation.name"
        :class="[ROW, BODY_ROW]"
      >
        <div class="flex min-w-0 items-center gap-2">
          <div
            class="flex size-7 shrink-0 items-center justify-center rounded-full border border-dashed border-outline-gray-3"
          >
            <LucideMail class="size-3.5 text-ink-gray-5" />
          </div>
          <div class="min-w-0">
            <div class="truncate text-base-medium text-ink-gray-8">
              {{ invitation.email }}
            </div>
            <div class="truncate text-p-sm text-ink-gray-5">
              {{ invitedLabel(invitation) }}
            </div>
          </div>
        </div>

        <span class="text-base text-ink-gray-5">{{
          roleLabel(invitation.role)
        }}</span>

        <div
          v-if="showLastActive"
          class="text-p-sm text-ink-gray-5 max-sm:hidden"
        >
          {{ __("Pending") }}
        </div>

        <div :class="ACTIONS">
          <Tooltip :text="__('Cancel invitation')">
            <Button
              variant="ghost"
              icon="lucide-x"
              :aria-label="__('Cancel invitation')"
              @click="emit('cancel', invitation)"
            />
          </Tooltip>
        </div>
      </div>

      <div
        v-if="!matches.length && !matchingInvitations.length"
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
  Skeleton,
  TextInput,
  Tooltip,
} from "frappe-ui";
import LucideMail from "~icons/lucide/mail";
import LucideSearch from "~icons/lucide/search";
import LucideUsers from "~icons/lucide/users";
import { __ } from "@helpdesk/shared/translation";
import { matchesQuery, timeAgo } from "@helpdesk/shared/utils";
import {
  ASSIGNABLE_ROLES,
  ROLES,
  roleLabel,
  type RoleLabel,
} from "@app/stores/settings/roles";

// Matches PortalOrganizationTickets.vue so both tabs line up.
const ROW = computed(() => [
  "grid items-center gap-3 border-b border-outline-gray-1 px-0.5 last:border-b-0",
  props.showLastActive
    ? "grid-cols-[minmax(0,1fr)_104px_32px] sm:grid-cols-[minmax(0,1fr)_104px_120px_32px]"
    : "grid-cols-[minmax(0,1fr)_104px_32px]",
]);

const BODY_ROW = "min-h-13 py-2.5";
const BLOCK = "motion-reduce:animate-none";

const ACTIONS = "flex justify-end";

type Member = {
  contact?: string;
  full_name: string;
  email?: string;
  image?: string;
  last_active?: string;
  role: RoleLabel;
  is_you?: boolean;
};

type Invitation = {
  name: string;
  email: string;
  role: RoleLabel;
  invited_by?: string;
  invited_by_you?: boolean;
  invited_on?: string;
};

// No Owner filter: one per org, listed right after you.
const roleFilters = computed(() => [
  { label: __("All"), value: "All", icon: LucideUsers },
  ...ASSIGNABLE_ROLES.map((role) => ({
    label: roleLabel(role),
    value: role,
    icon: ROLES[role].icon,
  })),
  ...(props.invitations.length
    ? [{ label: __("Invited"), value: "Invited", icon: LucideMail }]
    : []),
]);

const props = withDefaults(
  defineProps<{
    members?: Member[];
    invitations?: Invitation[];
    canManageMembers?: boolean;
    showLastActive?: boolean;
    loading?: boolean;
  }>(),
  {
    members: () => [],
    invitations: () => [],
    canManageMembers: false,
  }
);

const emit = defineEmits<{
  setRole: [member: Member, role: RoleLabel];
  remove: [member: Member];
  cancel: [invitation: Invitation];
}>();

const role = ref("All");
const search = ref("");

const matches = computed(() =>
  props.members.filter((member) => matchesRole(member) && matchesSearch(member))
);

const matchingInvitations = computed(() =>
  ["All", "Invited"].includes(role.value)
    ? props.invitations.filter((invitation) =>
        matchesQuery(search.value, invitation.email)
      )
    : []
);

function matchesRole(member: Member) {
  return role.value === "All" || member.role === role.value;
}

function matchesSearch(member: Member) {
  return matchesQuery(search.value, member.full_name, member.email);
}

function lastActive(member: Member) {
  return member.last_active ? timeAgo(member.last_active) : __("Never");
}

function invitedLabel(invitation: Invitation) {
  const when = timeAgo(invitation.invited_on);
  return invitation.invited_by_you
    ? __("Invited {0} by you", [when])
    : __("Invited {0} by {1}", [when, invitation.invited_by]);
}

// Owner is fixed; changing yourself would revoke the needed rights.
function canManage(member: Member) {
  return props.canManageMembers && member.role !== "Owner" && !member.is_you;
}

function memberOptions(member: Member) {
  return [
    {
      label: __("Change role"),
      icon: "lucide-user-cog",
      submenu: ASSIGNABLE_ROLES.map((role) => ({
        label: roleLabel(role),
        icon: ROLES[role].icon,
        selected: member.role === role,
        onClick: () => member.role !== role && emit("setRole", member, role),
      })),
    },
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
