<template>
  <div v-if="actions?.length" class="flex items-center gap-2">
    <!-- `icon` would make it icon-only, so it goes in the prefix -->
    <Button
      v-for="action in buttons"
      :key="action.label"
      v-bind="{ ...action, icon: undefined }"
    >
      <template v-if="action.icon" #prefix>
        <StoredIcon :icon="action.icon" class="size-4" />
      </template>
    </Button>
    <Dropdown
      v-for="group in labelledGroups"
      :key="group.label"
      v-slot="{ open }"
      :options="group.options"
    >
      <Button :label="group.label">
        <template #suffix>
          <Icon
            :icon="open ? 'lucide-chevron-up' : 'lucide-chevron-down'"
            class="size-4"
          />
        </template>
      </Button>
    </Dropdown>
    <Dropdown v-if="moreOptions.length" :options="moreOptions">
      <Button
        icon="lucide-more-horizontal"
        variant="ghost"
        :label="__('More actions')"
      />
    </Dropdown>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { Button, Dropdown, Icon } from "frappe-ui";
import StoredIcon from "@helpdesk/shared/Icon.vue";
import { __ } from "@helpdesk/shared/translation";
import { useMediaQuery } from "@vueuse/core";

const props = defineProps<{ actions?: any[] }>();
const isNarrow = useMediaQuery("(max-width: 767px)");

const plainActions = computed(() =>
  (props.actions || []).filter((a) => !a.group)
);
// Narrow screens fold buttons and labelled menus into "…".
const buttons = computed(() => (isNarrow.value ? [] : plainActions.value));

const groupsByLabel = computed(() => {
  const groups = new Map<string, any[]>();
  for (const action of props.actions || []) {
    if (!action.group || !action.buttonLabel) continue;
    groups.set(action.buttonLabel, [
      ...(groups.get(action.buttonLabel) || []),
      action,
    ]);
  }
  return [...groups].map(([label, options]) => ({ label, options }));
});

const labelledGroups = computed(() =>
  isNarrow.value ? [] : groupsByLabel.value
);

const moreOptions = computed(() => [
  // Grouped actions are already menu groups, so they nest as-is.
  ...(isNarrow.value
    ? [...plainActions.value, ...groupsByLabel.value.flatMap((g) => g.options)]
    : []),
  ...(props.actions || []).filter((a) => a.group && !a.buttonLabel),
]);
</script>
