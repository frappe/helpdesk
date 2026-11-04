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
      <div class="grid w-64 grid-cols-7 gap-1 p-1">
        <Button
          v-for="value in CATEGORY_ICONS"
          :key="value"
          :icon="value"
          :variant="value === icon ? 'subtle' : 'ghost'"
          :aria-label="value.replace('lucide-', '').replace(/-/g, ' ')"
          :aria-pressed="value === icon"
          @click="pick(value)"
        />
      </div>
    </template>
  </Popover>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { Button, Popover } from "frappe-ui";
import { CATEGORY_ICONS, categoryIcon } from "@helpdesk/shared/categoryIcons";
import { __ } from "@/translation";

const icon = defineModel<string>({ default: "lucide-folder" });
const open = ref(false);

function pick(value: string) {
  icon.value = value;
  open.value = false;
}
</script>
