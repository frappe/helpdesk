<template>
  <div class="flex flex-col">
    <PageTitle title="Knowledge base" />
    <div class="flex grow border-t">
      <div
        class="h-full space-y-2 border-r px-3.5 py-2.5"
        :style="{
          width: '242px',
        }"
      >
        <div class="flex items-center justify-between">
          <div class="text-sm font-medium text-gray-600">Categories</div>
          <Button theme="gray" variant="ghost">
            <template #icon>
              <IconMoreHorizontal class="h-4 w-4" />
            </template>
          </Button>
        </div>
        <LinkGroup :options="categories" />
      </div>
      <KnowledgeBaseCategory />
    </div>
  </div>
</template>

<script setup lang="ts">
import { Button } from "frappe-ui";
import PageTitle from "@/components/PageTitle.vue";
import LinkGroup from "@/components/desk/sidebar/LinkGroup.vue";
import KnowledgeBaseCategory from "./KnowledgeBaseCategory.vue";
import IconBox from "~icons/lucide/box";
import IconMoreHorizontal from "~icons/lucide/more-horizontal";

const categories = Array(5)
  .fill(1)
  .map(() => ({
    icon: IconBox,
    label: "Getting started",
    onClick: () => console.log("clicked"),
  }));
</script>
