<template>
  <!-- Links, not tabs: these screens live in the agent portal's own settings. -->
  <div class="space-y-4">
    <SettingsNavGroup
      v-for="group in groups"
      :key="group.label"
      :label="group.label"
    >
      <a
        v-for="link in group.links"
        :key="link.href"
        :href="link.href"
        class="group flex h-7 w-full items-center gap-2 rounded-4 px-2 text-left text-base text-ink-gray-7 hover:bg-surface-gray-2"
      >
        <span :class="[link.icon, 'size-4 shrink-0']" aria-hidden="true" />
        <span class="min-w-0 flex-1 truncate">{{ link.label }}</span>
        <span
          class="lucide-arrow-up-right size-4 shrink-0 text-ink-gray-4 opacity-0 group-hover:opacity-100"
          aria-hidden="true"
        />
      </a>
    </SettingsNavGroup>
  </div>
</template>

<script setup lang="ts">
import { SettingsNavGroup } from "frappe-ui";

type AgentSettingsGroup = {
  label: string;
  links: { label: string; icon: string; href: string }[];
};

defineProps<{ groups: AgentSettingsGroup[] }>();
</script>
