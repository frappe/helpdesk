<template>
  <AvatarRow
    v-bind="props"
    class="pt-1.5"
    :upload-options="{ private: false, optimize: true }"
  >
    <slot />
  </AvatarRow>
</template>

<script setup lang="ts">
// Studio only finds custom blocks under the app folder.
import AvatarRow from "@helpdesk/shared/AvatarRow.vue";

const props = withDefaults(
  defineProps<{
    name?: string;
    subtitle?: string;
    image?: string;
    shape?: "circle" | "square";
    busy?: boolean;
    editable?: boolean;
    renameable?: boolean;
  }>(),
  { shape: "circle", editable: true, renameable: true }
);
</script>
