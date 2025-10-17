<template>
  <div>
    <div class="px-10 py-8">
      <SettingsLayoutHeader :description="description">
        <template #title>
          <div class="flex items-center gap-2">
            <Button
              v-if="showBackButton"
              variant="ghost"
              icon-left="chevron-left"
              :label="title"
              size="md"
              @click="$emit('back')"
              class="cursor-pointer -ml-4 hover:bg-transparent focus:bg-transparent focus:outline-none focus:ring-0 focus:ring-offset-0 focus-visible:none active:bg-transparent active:outline-none active:ring-0 active:ring-offset-0 active:text-ink-gray-5 font-semibold text-ink-gray-7 text-lg hover:opacity-70 !pr-0"
            />

            <h1 v-else class="text-lg font-semibold text-ink-gray-8">
              {{ title }}
            </h1>
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
            <Switch
              v-if="showEnabledSwitch"
              size="sm"
              :label="__('Enabled')"
              :model-value="modelValue"
              @update:modelValue="(val) => emit('update:modelValue', val)"
              :style="{ background: 'transparent', padding: '0px' }"
              class="flex-row-reverse gap-x-2 pl-0"
            />
            <Button
              label="Save"
              theme="gray"
              variant="solid"
              @click="$emit('save')"
              :disabled="!isDirty"
              :loading="isSaving"
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
import { computed } from "vue";
import SettingsLayoutHeader from "../SettingsLayoutHeader.vue";
import { Badge, Button, Switch } from "frappe-ui";

// Use a computed property for v-model: modelValue <-> update:modelValue
const props = defineProps<{
  title: string;
  description: string;
  isDirty: boolean;
  isSaving: boolean;
  modelValue?: boolean;
  showBackButton?: boolean;
  showEnabledSwitch?: boolean;
}>();

const emit = defineEmits(["update:modelValue", "back", "save"]);
</script>
