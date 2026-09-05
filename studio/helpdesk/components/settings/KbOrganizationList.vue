<template>
  <div>
    <!-- Wrapped rather than styled directly: scoped rules don't reach a child
         component's own root, so the spacing lives on an element of ours. -->
    <div class="mb-6">
      <TextInput v-model="search" type="text" :placeholder="t('Search')">
        <template #prefix>
          <LucideSearch class="size-4 text-ink-gray-5" />
        </template>
      </TextInput>
    </div>

    <KbEmptyState
      v-if="!matches.length"
      icon="organization"
      :title="search ? 'No organizations found' : 'No organizations'"
      :description="
        search
          ? 'Change your search terms.'
          : `You'll see your organization here once someone adds you to one.`
      "
    />

    <!-- Cards wide enough that "n tickets · n members" stays on one line. -->
    <div v-else class="grid grid-cols-[repeat(auto-fill,minmax(210px,1fr))] gap-3">
      <!-- On hover the elevation token draws its own hairline, so the resting
           border gives way — keeping both double-draws the edge instead of lifting. -->
      <div
        v-for="organization in matches"
        :key="organization.name"
        class="cursor-pointer rounded-[10px] border border-outline-gray-1 p-4 transition-[box-shadow,border-color] duration-150 hover:border-transparent hover:bg-surface-elevation-1 hover:shadow-[var(--elevation-sm)]"
        role="button"
        tabindex="0"
        @click="onSelect?.(organization.name)"
        @keydown.enter="onSelect?.(organization.name)"
      >
        <div class="mb-3 flex items-start justify-between gap-2">
          <Avatar
            shape="square"
            size="3xl"
            :image="organization.image"
            :label="organization.customer_name"
          />
          <Badge
            v-if="organization.role"
            :label="organization.role"
            :theme="roleTheme(organization.role)"
            variant="outline"
          />
        </div>
        <div class="overflow-hidden text-ellipsis whitespace-nowrap text-[15px] font-semibold leading-5 text-ink-gray-9">
          {{ organization.customer_name }}
        </div>
        <div class="mt-0.5 overflow-hidden text-ellipsis whitespace-nowrap text-p-base text-ink-gray-5">{{ organization.domain }}</div>
        <div class="mt-3 flex items-center gap-1.5 border-t border-outline-gray-1 pt-3 text-p-sm text-ink-gray-5">
          <span class="flex items-center gap-1 whitespace-nowrap">
            <LucideTicket class="size-3.5 shrink-0" />
            {{ count(organization.ticket_count, "ticket") }}
          </span>
          <span class="text-ink-gray-4">·</span>
          <span class="flex items-center gap-1 whitespace-nowrap">
            <LucideSquareUser class="size-3.5 shrink-0" />
            {{ count(organization.member_count, "member") }}
          </span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { t } from "@app/stores/translations";
// A card per organization, each carrying a role badge — Owner, Manager or
// Member — rather than being sorted into sections.
import { Avatar, Badge, TextInput } from "frappe-ui";
import LucideSearch from "~icons/lucide/search";
import LucideSquareUser from "~icons/lucide/square-user";
import LucideTicket from "~icons/lucide/ticket";
import { computed, ref } from "vue";
import KbEmptyState from "@app/components/shared/KbEmptyState.vue";

type Organization = {
  name: string;
  customer_name: string;
  domain?: string;
  image?: string;
  role?: string;
  member_count?: number;
  ticket_count?: number;
};

const props = withDefaults(
  defineProps<{
    organizations?: Organization[];
    /** Called with the organization's docname when one is picked. */
    onSelect?: (name: string) => void;
  }>(),
  { organizations: () => [] }
);

const search = ref("");

const matches = computed(() => {
  const query = search.value.trim().toLowerCase();
  if (!query) return props.organizations;
  return props.organizations.filter((organization) =>
    `${organization.customer_name} ${organization.domain || ""}`
      .toLowerCase()
      .includes(query)
  );
});

// Owner and Manager both act on the organization, so they get colour; a plain
// member stays neutral.
const ROLE_THEMES = { Owner: "blue", Manager: "green" };

function roleTheme(role: string) {
  return ROLE_THEMES[role] || "gray";
}

function count(total: number | undefined, noun: string) {
  return `${total || 0} ${total === 1 ? noun : noun + "s"}`;
}
</script>
