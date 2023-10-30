<template>
  <PageTitle>
    <template #title>
      <BreadCrumbs
        :items="[
          {
            label: 'Tickets',
            route: {
              name: parent,
            },
          },
          {
            label: title,
          },
        ]"
      />
    </template>
    <template #right>
      <slot name="right" />
    </template>
  </PageTitle>
</template>

<script setup lang="ts">
import { BreadCrumbs, PageTitle } from "@/components";

defineProps<{
  parent: string;
  title: string;
}>();
</script>
