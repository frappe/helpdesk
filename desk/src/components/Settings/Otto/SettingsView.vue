<template>
  <div>
    <div class="px-10 py-8">
      <SettingsLayoutHeader :description="description">
        <template #title>
          <div class="flex items-center gap-2">
            <h1 class="text-lg font-semibold text-ink-gray-8">{{ title }}</h1>
            <Badge
              :class="[isDirty ? 'opacity-100' : 'opacity-0']"
              label="Unsaved"
              theme="orange"
              variant="subtle"
            />
          </div>
        </template>
        <template #actions>
          <div class="flex items-center gap-2">
            <Button
              v-if="showBackButton"
              icon="chevron-left"
              variant="subtle"
              @click="$emit('back')"
            />
            <Button
              label="Save"
              theme="gray"
              variant="solid"
              @click="$emit('save')"
              :disabled="!isDirty"
              :loading="saving"
            />
          </div>
        </template>
      </SettingsLayoutHeader>
    </div>
    <div class="px-10 pb-8 overflow-y-auto">
      <slot />
    </div>
  </div>
</template>

<script setup lang="ts">
import SettingsLayoutHeader from "../SettingsLayoutHeader.vue";
import { Badge, Button } from "frappe-ui";

defineProps<{
  title: string;
  description: string;
  isDirty: boolean;
  saving: boolean;
  showBackButton?: boolean;
}>();

defineEmits<{
  back: [];
  save: [];
}>();
</script>
