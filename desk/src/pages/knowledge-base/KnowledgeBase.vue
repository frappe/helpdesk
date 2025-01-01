<template>
  <div class="flex flex-col">
    <LayoutHeader>
      <template #left-header>
        <div class="text-lg font-medium text-gray-900">Knowledge base</div>
      </template>
      <template #right-header>
        <Button
          label="New article"
          variant="solid"
          @click="() => $router.push('/articles/new')"
        >
          <template #prefix>
            <LucidePlus class="h-4 w-4" />
          </template>
        </Button>
      </template>
    </LayoutHeader>
    <div class="flex grow"></div>
  </div>
</template>

<script setup lang="ts">
import { usePageMeta } from "frappe-ui";
import LayoutHeader from "@/components/LayoutHeader.vue";

usePageMeta(() => {
  return {
    title: "Knowledge base",
  };
});
</script>
