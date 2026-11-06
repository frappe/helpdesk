<template>
  <Badge v-if="meta" theme="gray" :label="meta.label" class="shrink-0">
    <template #prefix>
      <Icon :icon="meta.icon" class="size-3" aria-hidden="true" />
    </template>
  </Badge>
</template>

<script setup lang="ts">
import { Badge } from "frappe-ui";
import { computed } from "vue";
import Icon from "../Icon.vue";
import { categoryAccess } from "./categoryAccess";

const props = defineProps<{ access?: string }>();

const meta = computed(() => props.access && categoryAccess()[props.access]);
</script>
