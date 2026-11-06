<template>
  <Popover
    v-model:open="open"
    align="start"
    :trigger="field ? 'manual' : 'click'"
    :auto-focus="!field"
  >
    <template #trigger>
      <TextInput
        v-if="field"
        v-model="fieldValue"
        class="w-full [&_input:focus]:bg-surface-gray-2 [&_input:focus]:ring-2 [&_input:focus]:ring-outline-gray-3"
        autocomplete="off"
        :placeholder="fieldPlaceholder"
        :aria-label="__('Choose an icon')"
        @focus="open = true"
        @click="open = true"
        @keydown.delete="clearIcon"
      >
        <template #prefix>
          <Icon :icon="icon || 'lucide-circle-dashed'" class="size-4" />
        </template>
        <template #suffix>
          <span class="lucide-chevron-down size-4 text-ink-gray-5" />
        </template>
      </TextInput>
      <Button
        v-else
        variant="subtle"
        size="md"
        :icon="categoryIcon(icon)"
        :aria-label="__('Choose an icon')"
        class="shrink-0"
      />
    </template>
    <template #default>
      <div class="w-[19.5rem] max-w-[calc(100vw-2rem)] p-2">
        <TextInput
          v-if="!field"
          v-model="query"
          v-focus
          class="mb-2"
          :placeholder="__('Search icons')"
          :aria-label="__('Search icons')"
        />
        <ScrollArea viewport-class="max-h-72">
          <div class="grid grid-cols-8 gap-1">
            <Button
              v-for="value in matches"
              :key="value"
              :icon="value"
              :variant="value === icon ? 'subtle' : 'ghost'"
              :title="iconLabel(value)"
              :aria-label="iconLabel(value)"
              :aria-pressed="value === icon"
              @click="pick(value)"
            />
          </div>
        </ScrollArea>
        <p v-if="!matches.length" class="px-1 py-4 text-p-sm text-ink-gray-5">
          {{ __("No icons found") }}
        </p>
      </div>
    </template>
  </Popover>
</template>

<script setup lang="ts">
import { computed, ref, watch } from "vue";
import { Button, Popover, ScrollArea, TextInput, vFocus } from "frappe-ui";
import { CATEGORY_ICONS, categoryIcon } from "./categoryIcons";
import Icon from "./Icon.vue";
import { __ } from "./translation";

// `field` shows a full-width input that searches as you type.
const props = defineProps<{ field?: boolean; placeholder?: string }>();

const icon = defineModel<string>();
const open = ref(false);
const query = ref("");

const iconLabel = (value: string) =>
  value.replace("lucide-", "").replace(/-/g, " ");
const iconTitle = (value?: string) =>
  iconLabel(value || "").replace(/\b\w/g, (char) => char.toUpperCase());
const fieldPlaceholder = computed(
  () => iconTitle(icon.value) || props.placeholder || __("Select an icon...")
);
const fieldValue = computed({
  get: () => (open.value ? query.value : iconTitle(icon.value)),
  set: (value: string) => {
    query.value = value;
    open.value = true;
  },
});
const matches = computed(() => {
  const needle = query.value.trim().toLowerCase();
  return CATEGORY_ICONS.filter((value) => iconLabel(value).includes(needle));
});

watch(open, () => (query.value = ""));

// Deleting past an empty search clears the icon.
function clearIcon() {
  if (!query.value) icon.value = "";
}

function pick(value: string) {
  icon.value = value;
  open.value = false;
}
</script>
