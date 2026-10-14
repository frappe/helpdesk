<template>
  <div v-if="actions?.length" class="flex items-center gap-2">
    <!-- onClick rides along in `action`; `icon` would make it an icon-only button -->
    <Button
      v-for="action in buttons"
      :key="action.label"
      v-bind="{ ...action, icon: undefined }"
    >
      <template v-if="typeof action.icon === 'string'" #prefix>
        <ScriptIcon :icon="action.icon" />
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
import { ScriptIcon } from "./formScripts";
import { __ } from "./translation";
import { useMediaQuery } from "@vueuse/core";

// Header actions from HD Form Scripts, on the desk and the portal: a plain action is a button, `group` with
// `buttonLabel` a labelled menu, and `group` alone goes under "…".
const props = defineProps<{ actions?: any[] }>();
const isNarrow = useMediaQuery("(max-width: 767px)");

const plainActions = computed(() =>
  (props.actions || []).filter((a) => !a.group)
);
// Below md the header has no room for buttons beside the logo, crumbs and sign-in.
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

// Below md labelled menus fold into "…" as well, or they push the logo menu off a phone screen.
const labelledGroups = computed(() => (isNarrow.value ? [] : groupsByLabel.value));

const moreOptions = computed(() => [
  // A grouped action is itself a menu group, so a labelled menu's entries drop in as they are.
  ...(isNarrow.value
    ? [...plainActions.value, ...groupsByLabel.value.flatMap((g) => g.options)]
    : []),
  ...(props.actions || []).filter((a) => a.group && !a.buttonLabel),
]);
</script>
