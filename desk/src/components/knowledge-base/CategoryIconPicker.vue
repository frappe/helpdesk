<template>
  <Popover v-model:open="open">
    <template #trigger>
      <Button
        variant="subtle"
        size="md"
        :icon="categoryIcon(icon)"
        :aria-label="__('Choose an icon')"
        class="shrink-0"
      />
    </template>
    <template #default>
      <div class="w-64 p-1">
        <TextInput
          v-model="query"
          v-focus
          class="mb-1"
          :placeholder="__('Search icons')"
          :aria-label="__('Search icons')"
        />
        <div class="grid max-h-64 grid-cols-7 gap-1 overflow-y-auto">
          <Button
            v-for="value in matches"
            :key="value"
            :icon="value"
            :variant="value === icon ? 'subtle' : 'ghost'"
            :aria-label="iconLabel(value)"
            :aria-pressed="value === icon"
            @click="pick(value)"
          />
        </div>
        <p v-if="!matches.length" class="px-1 py-4 text-p-sm text-ink-gray-5">
          {{ __("No icons found") }}
        </p>
      </div>
    </template>
  </Popover>
</template>

<script setup lang="ts">
import { computed, ref, watch } from "vue";
import { Button, Popover, TextInput, vFocus } from "frappe-ui";
import { CATEGORY_ICONS, categoryIcon } from "@helpdesk/shared/categoryIcons";
import { __ } from "@/translation";

const icon = defineModel<string>({ default: "lucide-folder" });
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
