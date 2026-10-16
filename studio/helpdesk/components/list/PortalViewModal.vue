<template>
  <Dialog
    v-model:open="open"
    :title="isRename ? __('Rename view') : __('Save as new view')"
    :actions="[
      {
        label: isRename ? __('Save') : __('Create'),
        variant: 'solid',
        disabled: !label.trim(),
        onClick: () => emit('submit'),
      },
    ]"
  >
    <FormControl
      v-model="label"
      type="text"
      :label="__('Name')"
      :placeholder="__('My open tickets')"
      autocomplete="off"
      @keyup.enter="label.trim() && emit('submit')"
    />
    <ViewIconField v-model="icon" class="mt-4" />
    <p v-if="!isRename" class="mt-4 text-p-sm text-ink-gray-6">
      {{ __("Saves the filters, sort order and columns currently on screen.") }}
    </p>
  </Dialog>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { Dialog, FormControl } from "frappe-ui";
import ViewIconField from "@helpdesk/shared/ViewIconField.vue";
import { __ } from "@helpdesk/shared/translation";

const props = withDefaults(defineProps<{ mode?: "create" | "rename" }>(), {
  mode: "create",
});
const emit = defineEmits<{ submit: [] }>();

const open = defineModel<boolean>("open", { default: false });
const label = defineModel<string>("label", { default: "" });
const icon = defineModel<string>("icon", { default: "" });

const isRename = computed(() => props.mode === "rename");
</script>
