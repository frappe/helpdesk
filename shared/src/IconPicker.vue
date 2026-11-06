<template>
  <Popover v-model:open="open" align="start">
    <template #trigger>
      <slot>
        <Button
          variant="subtle"
          size="md"
          :icon="categoryIcon(icon)"
          :aria-label="__('Choose an icon')"
          class="shrink-0"
        />
      </slot>
    </template>
    <template #default>
      <div class="w-[19.5rem] max-w-[calc(100vw-2rem)] p-2">
        <TextInput
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
import { __ } from "./translation";

const icon = defineModel<string>();
const open = ref(false);
const query = ref("");

const iconLabel = (value: string) =>
  value.replace("lucide-", "").replace(/-/g, " ");
const matches = computed(() => {
  const needle = query.value.trim().toLowerCase();
  return CATEGORY_ICONS.filter((value) => iconLabel(value).includes(needle));
});

watch(open, () => (query.value = ""));

function pick(value: string) {
  icon.value = value;
  open.value = false;
}
</script>
