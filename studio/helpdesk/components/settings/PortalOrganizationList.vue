<template>
  <div>
    <div class="mb-3">
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

    <div v-else>
      <div
        :class="[
          ROW,
          'h-8 rounded-5 bg-surface-gray-2 px-3 text-p-sm text-ink-gray-5',
        ]"
      >
        <span>{{ __("Name") }}</span>
        <span>{{ __("Role") }}</span>
        <span class="max-sm:hidden">{{ __("Domain") }}</span>
        <span class="max-sm:hidden">{{ __("Members") }}</span>
        <span class="max-sm:hidden">{{ __("Tickets") }}</span>
      </div>

      <div
        v-for="organization in matches"
        :key="organization.name"
        class="group cursor-pointer rounded-5 px-3 hover:bg-surface-gray-2"
        role="button"
        tabindex="0"
        @click="emit('select', organization.name)"
        @keydown.enter="emit('select', organization.name)"
      >
        <div
          :class="[
            ROW,
            'min-h-14 border-b border-outline-gray-1 group-last:border-b-0',
          ]"
        >
          <div class="flex min-w-0 items-center gap-2.5">
            <Avatar
              shape="square"
              size="xl"
              :image="organization.image"
              :label="organization.customer_name"
            />
            <span class="truncate text-base-medium text-ink-gray-8">
              {{ organization.customer_name }}
            </span>
          </div>
          <div>
            <Badge
              v-if="organization.role"
              :label="roleLabel(organization.role)"
              :theme="ROLES[organization.role].theme"
              variant="subtle"
            />
          </div>
          <span class="truncate text-p-base text-ink-gray-5 max-sm:hidden">
            {{ organization.domain }}
          </span>
          <span class="text-p-base text-ink-gray-7 max-sm:hidden">
            {{ organization.member_count || 0 }}
          </span>
          <span class="text-p-base text-ink-gray-7 max-sm:hidden">
            {{ organization.ticket_count || 0 }}
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
import { __ } from "@helpdesk/shared/translation";
import PortalEmptyState from "@app/components/common/PortalEmptyState.vue";
import { ROLES, roleLabel, type RoleLabel } from "@app/stores/settings/roles";
import { matchesQuery } from "@app/utils";

const ROW =
  "grid grid-cols-[minmax(0,1fr)_88px] sm:grid-cols-[minmax(0,1fr)_88px_minmax(0,160px)_64px_64px] items-center gap-3";

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
