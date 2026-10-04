<template>
  <div class="w-full sm:w-[220px]">
    <!-- The width sits on a wrapper: MultiSelect hands its class to the trigger, not its root. -->
    <MultiSelect
      class="w-full"
      size="sm"
      variant="subtle"
      align="start"
      :placeholder="__('Select organizations')"
      :options="options"
      :model-value="selectedOrganizations"
      @update:model-value="(value) => emit('select', value)"
    >
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

      <!-- `#item`, so the tick sits after the name; MultiSelect hard-codes it before. -->
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
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { Avatar, Checkbox, ItemListRow, MultiSelect } from "frappe-ui";
import LucideBuilding2 from "~icons/lucide/building-2";
import { __ } from "@helpdesk/shared/translation";

type Organization = { name: string; customer_name?: string; image?: string };

const props = withDefaults(
  defineProps<{
    organizations?: Organization[];
    selectedOrganizations?: string[];
  }>(),
  { organizations: () => [], selectedOrganizations: () => [] }
);
const emit = defineEmits<{ select: [names: string[]] }>();

const options = computed(() =>
  props.organizations.map((organization) => ({
    label: organization.customer_name || organization.name,
    value: organization.name,
    image: organization.image,
  }))
);
</script>
