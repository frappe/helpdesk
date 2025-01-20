<template>
  <router-link
    class="flex flex-col gap-3 border border-gray-200 rounded p-4 pb-2 cursor-pointer h-30 hover:bg-surface-gray-2 transition-all"
    :to="{
      name: 'ArticlePublic',
      params: {
        articleId: article.name,
      },
    }"
  >
    <!-- Title and sub content -->
    <div class="flex gap-3 flex-1">
      <div class="flex flex-col gap-1.5 w-full">
        <h5 class="text-base font-medium text-gray-800 truncate">
          {{ article.title }}
        </h5>
        <div class="text-p-sm text-gray-600 line-clamp-2">
          {{ article.content }}
        </div>
      </div>
    </div>
    <!-- Avatar and published date -->
    <div class="flex justify-between items-center">
      <div class="flex gap-2 items-center">
        <Avatar :label="article.author.name" :image="article.author.image" />
        <span class="text-sm text-gray-600 flex-1 truncate">{{
          article.author.name
        }}</span>
      </div>
      <span class="text-sm text-gray-600">{{
        dayjs.tz(article.modified).fromNow()
      }}</span>
    </div>
  </router-link>
</template>

<script setup lang="ts">
import { Avatar } from "frappe-ui";
import { Article } from "@/types";
import { dayjs } from "@/dayjs";

const props = defineProps<{
  article: Article;
}>();
</script>
