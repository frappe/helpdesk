<template>
  <div>
    <div class="mb-6">
      <TextInput v-model="search" type="text" :placeholder="__('Search')">
        <template #prefix>
          <LucideSearch class="size-4 text-ink-gray-5" />
        </template>
      </TextInput>
    </div>

    <PortalEmptyState
      v-if="!matches.length"
      icon="organization"
      v-bind="emptyState"
    />

    <div
      v-else
      class="grid grid-cols-[repeat(auto-fill,minmax(210px,1fr))] gap-3"
    >
      <div
        v-for="organization in matches"
        :key="organization.name"
        class="cursor-pointer rounded-[10px] border border-outline-gray-1 p-4 transition-[box-shadow,border-color] duration-150 hover:border-transparent hover:bg-surface-elevation-1 hover:shadow-[var(--elevation-sm)]"
        role="button"
        tabindex="0"
        @click="emit('select', organization.name)"
        @keydown.enter="emit('select', organization.name)"
      >
        <div class="mb-3 flex items-start justify-between gap-2">
          <Avatar
            class="has-[>div:first-child]:border has-[>div:first-child]:border-outline-gray-2"
            shape="square"
            size="3xl"
            :image="organization.image"
            :label="organization.customer_name"
          />
          <Badge
            v-if="organization.role"
            :label="roleLabel(organization.role)"
            :theme="ROLES[organization.role]?.theme || 'gray'"
            variant="subtle"
          />
        </div>
        <div
          class="truncate text-[15px] font-semibold leading-5 text-ink-gray-9"
        >
          {{ organization.customer_name }}
        </div>
        <div class="mt-0.5 truncate text-p-base text-ink-gray-5">
          {{ organization.domain }}
        </div>
        <div
          class="mt-3 flex items-center gap-1.5 border-t border-outline-gray-1 pt-3 text-p-sm text-ink-gray-5"
        >
          <span class="flex items-center gap-1 whitespace-nowrap">
            <LucideTicket class="size-3.5 shrink-0" />
            {{
              countLabel(
                organization.ticket_count || 0,
                __("1 ticket"),
                __("{0} tickets")
              )
            }}
          </span>
          <span class="text-ink-gray-4">·</span>
          <span class="flex items-center gap-1 whitespace-nowrap">
            <LucideSquareUser class="size-3.5 shrink-0" />
            {{
              countLabel(
                organization.member_count || 0,
                __("1 member"),
                __("{0} members")
              )
            }}
          </span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";
import { Avatar, Badge, TextInput } from "frappe-ui";
import LucideSearch from "~icons/lucide/search";
import LucideSquareUser from "~icons/lucide/square-user";
import LucideTicket from "~icons/lucide/ticket";
import { __ } from "@helpdesk/shared/translation";
import PortalEmptyState from "@app/components/common/PortalEmptyState.vue";
import { ROLES, roleLabel, type RoleLabel } from "@app/stores/settings/roles";
import { countLabel, matchesQuery } from "@app/utils";

type Organization = {
  name: string;
  customer_name: string;
  domain?: string;
  image?: string;
  role?: RoleLabel;
  member_count?: number;
  ticket_count?: number;
};

const props = withDefaults(defineProps<{ organizations?: Organization[] }>(), {
  organizations: () => [],
});
const emit = defineEmits<{ select: [name: string] }>();

const search = ref("");

const emptyState = computed(() =>
  search.value
    ? {
        title: __("No organizations found"),
        description: __("Change your search terms."),
      }
    : {
        title: __("No organizations"),
        description: __(
          "You'll see your organization here once someone adds you to one."
        ),
      }
);

const matches = computed(() =>
  props.organizations.filter((organization) =>
    matchesQuery(search.value, organization.customer_name, organization.domain)
  )
);
</script>
