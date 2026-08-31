<template>
  <!-- One width for the trigger and its menu: organization names vary in length,
       so a hugging trigger made the control resize on every change. -->
  <MultiSelect
    class="kb-org-switcher"
    size="sm"
    variant="subtle"
    align="start"
    :placeholder="PLACEHOLDER"
    :options="options"
    :model-value="selectedOrganizations"
    @update:model-value="(value) => onSelect?.(value)"
  >
    <!-- Owns the whole prefix area, so one template covers none / one / many:
         a logo when a single organization is picked, the generic mark otherwise. -->
    <template #prefix="{ selectedOptions }">
      <Avatar
        v-if="selectedOptions.length === 1"
        size="xs"
        shape="square"
        :image="selectedOptions[0].image"
        :label="selectedOptions[0].label"
      />
      <LucideBuilding2 v-else class="size-4 text-ink-gray-5" />
    </template>

    <!-- Full-row takeover, so the tick sits after the name instead of before it.
         MultiSelect hard-codes its checkbox into the row's prefix, but it also
         documents `#item` for exactly this — so the row is still built from
         frappe-ui's own ItemListRow and Checkbox rather than moved with CSS. -->
    <template #item="{ item, selected }">
      <ItemListRow size="sm" :selected="selected" :disabled="item.disabled">
        <template #prefix>
          <Avatar
            size="sm"
            shape="square"
            :image="item.image"
            :label="item.label"
          />
        </template>
        <template #label>
          <div class="truncate">{{ item.label }}</div>
        </template>
        <template #suffix>
          <!-- Presentational: the row itself owns the click and the focus ring. -->
          <Checkbox
            :model-value="selected"
            :disabled="item.disabled"
            size="sm"
            tabindex="-1"
            aria-hidden="true"
            class="pointer-events-none"
          />
        </template>
      </ItemListRow>
    </template>
  </MultiSelect>
</template>

<script setup lang="ts">
// Organization switcher for the portal ticket list: the caller's organizations,
// any number of them at once, narrowing the list to those customers. Its value
// lives in the list's own filter conditions rather than beside them, so the
// Filter and QuickFilter controls and this switcher can never disagree.
import { Avatar, Checkbox, ItemListRow, MultiSelect } from "frappe-ui";
import LucideBuilding2 from "~icons/lucide/building-2";
import { computed } from "vue";

type Organization = { name: string; customer_name?: string; image?: string };

// MultiSelect drives both the empty trigger and the menu's search field from this one
// prop, so it reads as an invitation to pick rather than "All organizations" repeated
// back inside its own dropdown.
const PLACEHOLDER = "Select organizations";

const props = withDefaults(
  defineProps<{
    organizations?: Organization[];
    /** Docnames in play; empty means every organization. */
    selectedOrganizations?: string[];
    onSelect?: (names: string[]) => void;
  }>(),
  { organizations: () => [], selectedOrganizations: () => [] }
);

const options = computed(() =>
  props.organizations.map((organization) => ({
    label: organization.customer_name || organization.name,
    value: organization.name,
    image: organization.image,
  }))
);
</script>

<style>
/* Unscoped: the class lands on MultiSelect's own trigger, which carries no scope
   attribute of ours. Plain CSS because this app sits outside the bench's
   Tailwind content globs, so an arbitrary width class would not compile. */
.kb-org-switcher {
  width: 220px;
}
</style>
