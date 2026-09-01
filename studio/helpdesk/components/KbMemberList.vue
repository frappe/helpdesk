<template>
  <div>
    <div class="mb-3 flex items-center gap-2">
      <TextInput
        v-model="search"
        type="text"
        :placeholder="t('Search')"
        class="min-w-0 flex-1"
      >
        <template #prefix>
          <LucideSearch class="size-4 text-ink-gray-5" />
        </template>
      </TextInput>
      <!-- Each option carries its icon, so the trigger shows the role you filtered
           to rather than one generic glyph. Subtle, not outline: it sits beside the
           search and the pair reads as one strip — the outline variant's white fill and
           border made the filter the louder of the two. Both lighten on focus. -->
      <Select v-model="role" :options="ROLE_FILTERS" size="sm" />
    </div>

    <div>
      <div :class="[ROW, 'min-h-8 pt-0 text-p-xs text-ink-gray-5']">
        <span>{{ t("Members") }}</span>
        <span>{{ t("Last seen") }}</span>
        <span>{{ t("Role") }}</span>
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
            <div class="flex items-center gap-1.5 overflow-hidden text-ellipsis whitespace-nowrap text-base-medium text-ink-gray-8">
              {{ member.full_name }}
              <span v-if="member.is_you" class="text-p-xs font-normal text-ink-gray-5">You</span>
              <Badge
                v-if="member.pending"
                label="Pending"
                theme="orange"
                variant="subtle"
              />
            </div>
            <div class="overflow-hidden text-ellipsis whitespace-nowrap text-p-sm text-ink-gray-5">{{ member.email }}</div>
          </div>
        </div>

        <div class="text-p-sm text-ink-gray-5">{{ lastSeen(member) }}</div>

        <span class="inline-flex items-center gap-1.5 text-p-base text-ink-gray-7">
          <component :is="roleIcon(member)" class="size-4" />
          {{ roleLabel(member) }}
        </span>

        <div class="flex justify-end">
          <!-- `canRemove` is the wider of the two guards, so a row that has any
               action at all has this one. -->
          <Dropdown
            v-if="canRemove(member)"
            :options="rowOptions(member)"
            align="end"
          >
            <template #trigger="{ open }">
              <Button variant="ghost" icon="more-horizontal" :active="open" />
            </template>
          </Dropdown>
        </div>
      </div>

      <div v-if="!matches.length" class="py-6 text-center text-p-sm text-ink-gray-5">
        {{ t("No members match this filter.") }}
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { t } from "@app/stores/translations";
// The organization's people, one row each. Was a tree keyed on role, which implied
// a reporting line helpdesk does not record — any manager can act on any member.
import {
  Avatar,
  Badge,
  Button,
  Dropdown,
  Select,
  TextInput,
  dayjs,
} from "frappe-ui";
import LucideBriefcase from "~icons/lucide/briefcase";
import LucideCrown from "~icons/lucide/crown";
import LucideSearch from "~icons/lucide/search";
import LucideUser from "~icons/lucide/user";
import LucideUsers from "~icons/lucide/users";
import { computed, ref } from "vue";

// No container, no fills: rows are separated by a hairline and nothing else — and
// under the last row the hairline would be a line under nothing, hence last:border-b-0.
const ROW =
  "grid grid-cols-[minmax(0,1fr)_120px_132px_32px] items-center gap-3 border-b border-outline-gray-1 py-2 last:border-b-0";

type Member = {
  contact?: string;
  invitation?: string;
  full_name: string;
  email?: string;
  image?: string;
  last_seen?: string;
  is_manager?: boolean;
  is_owner?: boolean;
  is_you?: boolean;
  pending?: boolean;
};

const props = withDefaults(
  defineProps<{
    members?: Member[];
    /** Only a manager of this organization may change anyone. */
    canManage?: boolean;
    onSetRole?: (member: Member, role: string) => void;
    onRemove?: (member: Member) => void;
  }>(),
  { members: () => [], canManage: false }
);

const ROLE_ICONS = {
  Owner: LucideCrown,
  Manager: LucideBriefcase,
  Member: LucideUser,
};
// Owner is left out: there is exactly one per organization and the list already puts
// them first, so filtering to them narrows a list of four to a list of one.
const FILTERABLE_ROLES = ["Manager", "Member"];
const ROLE_FILTERS = [
  { label: "All", value: "All", icon: LucideUsers },
  ...FILTERABLE_ROLES.map((label) => ({
    label,
    value: label,
    icon: ROLE_ICONS[label],
  })),
];

const role = ref("All");
const search = ref("");

const matches = computed(() =>
  props.members.filter((member) => matchesRole(member) && matchesSearch(member))
);

function matchesRole(member: Member) {
  return role.value === "All" || roleLabel(member) === role.value;
}

function matchesSearch(member: Member) {
  const query = search.value.trim().toLowerCase();
  if (!query) return true;
  return `${member.full_name} ${member.email || ""}`
    .toLowerCase()
    .includes(query);
}

function roleLabel(member: Member) {
  if (member.is_owner) return "Owner";
  return member.is_manager ? "Manager" : "Member";
}

function roleIcon(member: Member) {
  return ROLE_ICONS[roleLabel(member)];
}

/** `User.last_active`, worded as the agent portal's contact page words it. Someone who
 *  has never signed in — anyone still holding an invitation — is said so in words: a dash
 *  reads as missing data where the absence is the fact. */
function lastSeen(member: Member) {
  return member.last_seen ? dayjs(member.last_seen).fromNow() : t("Never");
}

/** The owner's role is fixed, and demoting yourself revokes the rights the call
 *  needs. A pending invite carries its role until it is accepted. */
function canSwitchRole(member: Member) {
  return Boolean(
    props.canManage && !member.is_owner && !member.is_you && !member.pending
  );
}

function canRemove(member: Member) {
  return Boolean(props.canManage && !member.is_owner && !member.is_you);
}

/** Only what changes something: the role the member does not hold, and — for a
 *  pending invite, which holds none yet — the cancellation on its own. */
function rowOptions(member: Member) {
  if (member.pending) {
    return [
      {
        label: "Cancel invitation",
        icon: "x-circle",
        onClick: () => props.onRemove?.(member),
      },
    ];
  }
  const next = member.is_manager ? "Member" : "Manager";
  return [
    {
      label: next === "Manager" ? "Make manager" : "Make member",
      icon: ROLE_ICONS[next],
      onClick: () => props.onSetRole?.(member, next),
      condition: () => canSwitchRole(member),
    },
    {
      label: "Remove from organization",
      icon: "user-minus",
      onClick: () => props.onRemove?.(member),
    },
  ];
}

function keyOf(member: Member) {
  return member.contact || member.invitation || member.email;
}
</script>
