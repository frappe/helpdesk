<template>
  <router-link
    :to="{
      name: 'ArticlePublic',
      params: {
        articleId: article.name,
      },
    }"
  >
    <div class="flex justify-between items-center cursor-pointer w-full">
      <!-- Left Side -->
      <div class="flex p-2 gap-3 flex-1 max-w-[50%]">
        <div class="flex flex-col gap-1.5 w-full">
          <h5 class="text-lg font-semibold text-gray-800 truncate max-w-[70%]">
            {{ article.title }}
          </h5>
          <div class="text-sm text-gray-600 truncate max-w-[70%]">
            {{ articleSubTitle }}
          </div>
        </div>
      </div>

      <!-- Right Side -->
      <div class="flex flex-1 justify-between p-2 items-center gap-10">
        <div class="flex gap-2 items-center">
          <Avatar :label="article.author.name" :image="article.author.image" />
          <span class="text-sm text-gray-600 flex-1 truncate">{{
            article.author.name
          }}</span>
        </div>
        <span class="text-sm text-gray-600">{{
          dayjs.tz(article.published_on).format("DD, MMM YYYY")
        }}</span>
      </div>
    </div>
  </router-link>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { Avatar } from "frappe-ui";
import { dayjs } from "@/dayjs";
import { Article } from "@/types";

const props = defineProps<{
  article: Article;
}>();

const articleSubTitle = computed(
  () =>
    props.article.content ||
    "This article helps you understand the topic effectively."
);
</script>

<style scoped></style>
