<template>
  <div>
    <div class="kb-members__toolbar">
      <!-- Inline, not the scoped class: TextInput's root takes no scope id, so a
           scoped rule for it never matches. -->
      <TextInput
        v-model="search"
        type="text"
        :placeholder="t('Search')"
        :style="{ flex: 1, minWidth: 0 }"
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

    <div class="kb-members__table">
      <div class="kb-members__row kb-members__head">
        <span>{{ t("Members") }}</span>
        <span>{{ t("Last seen") }}</span>
        <span>{{ t("Role") }}</span>
        <span />
      </div>

      <div
        v-for="member in matches"
        :key="keyOf(member)"
        class="kb-members__row kb-members__body-row"
      >
        <div class="kb-members__person">
          <Avatar
            shape="circle"
            size="lg"
            :image="member.image"
            :label="member.full_name"
          />
          <div class="kb-members__identity">
            <div class="kb-members__name">
              {{ member.full_name }}
              <span v-if="member.is_you" class="kb-members__you">You</span>
              <Badge
                v-if="member.pending"
                label="Pending"
                theme="orange"
                variant="subtle"
              />
            </div>
            <div class="kb-members__email">{{ member.email }}</div>
          </div>
        </div>

        <div class="kb-members__last-seen">{{ lastSeen(member) }}</div>

        <span class="kb-members__role">
          <component :is="roleIcon(member)" class="size-4" />
          {{ roleLabel(member) }}
        </span>

        <div class="kb-members__actions">
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

      <div v-if="!matches.length" class="kb-members__empty">
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

<style scoped>
/* Plain CSS: this app sits outside the bench's Tailwind content globs, so only
   utilities the rest of the bundle already uses are safe here. */
.kb-members__toolbar {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
}

/* No container, no fills: rows are separated by a hairline and nothing else. */
.kb-members__row {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 120px 132px 32px;
  align-items: center;
  gap: 12px;
  padding: 8px 0;
  border-bottom: 1px solid var(--outline-gray-1);
}

/* A hairline separates two rows; under the last one it is a line under nothing. */
.kb-members__row:last-child {
  border-bottom: 0;
}

.kb-members__head {
  min-height: 32px;
  padding-top: 0;
  font-size: 12px;
  line-height: 16px;
  color: var(--ink-gray-5);
}

.kb-members__body-row {
  min-height: 52px;
}

.kb-members__role {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
  color: var(--ink-gray-7);
}

.kb-members__person {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
}

.kb-members__identity {
  min-width: 0;
}

.kb-members__name {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
  line-height: 20px;
  font-weight: 500;
  color: var(--ink-gray-8);
}

.kb-members__you {
  font-size: 12px;
  font-weight: 400;
  color: var(--ink-gray-5);
}

.kb-members__email,
.kb-members__last-seen {
  font-size: 13px;
  line-height: 18px;
  color: var(--ink-gray-5);
}

.kb-members__name,
.kb-members__email {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.kb-members__actions {
  display: flex;
  justify-content: flex-end;
}

.kb-members__empty {
  padding: 24px 0;
  text-align: center;
  font-size: 13px;
  color: var(--ink-gray-5);
}
</style>
