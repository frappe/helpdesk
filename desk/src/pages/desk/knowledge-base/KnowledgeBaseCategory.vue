<template>
  <div class="grow px-5 py-3.5">
    <div class="mb-6 space-y-1">
      <div class="flex items-center justify-between">
        <div class="text-xl font-medium text-gray-900">Getting started</div>
        <div class="space-x-2">
          <Button label="Edit" theme="gray" variant="outline"
            ><template #prefix><IconEdit class="h-4 w-4" /></template
          ></Button>
          <Button label="Add new" theme="gray" variant="solid"
            ><template #prefix><IconPlus class="h-4 w-4" /></template
          ></Button>
        </div>
      </div>
      <div
        class="text-base text-gray-700"
        :style="{
          width: '770px',
        }"
      >
        Lorem Ipsum is simply dummy text of the printing and typesetting
        industry. Lorem Ipsum has been the industry's standard dummy text ever
        since the 1500s.
      </div>
    </div>
    <div class="gap-5.5 grid grid-cols-3">
      <KnowledgeBaseCategoryCard
        v-for="i in 5"
        :key="i"
        class="place-self-center"
        title="Getting started"
        description="Lorem Ipsum is simply dummy text of the printing and typesetting industry."
        :article-count="13"
      />
    </div>
  </div>
</template>
<script setup lang="ts">
import { Button } from "frappe-ui";
import KnowledgeBaseCategoryCard from "./KnowledgeBaseCategoryCard.vue";
import IconEdit from "~icons/lucide/edit-3";
import IconPlus from "~icons/lucide/plus";
</script>
