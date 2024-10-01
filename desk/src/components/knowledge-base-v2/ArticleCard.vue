<template>
  <div class="flex justify-between items-center cursor-pointer w-full">
    <!-- Left Side -->
    <div class="flex p-2 gap-3 flex-1 max-w-[50%]">
      <Avatar label="JD" shape="square" size="2xl" :image="articleImg" />
      <div class="flex flex-col gap-1.5 w-full">
        <h5 class="text-lg font-semibold text-gray-800">
          {{ article.title }}
        </h5>
        <div
          class="text-sm text-gray-600 truncate overflow-hidden whitespace-nowrap overflow-ellipsis"
        >
          {{ articleSubTitle }}
        </div>
      </div>
    </div>

    <!-- Right Side -->
    <div class="flex flex-1 justify-between p-2 items-center gap-10">
      <div class="flex gap-1 items-center">
        <Avatar :label="author.name" :image="author.image" />
        <span class="text-sm text-gray-600 flex-1 truncate">{{
          author.name
        }}</span>
      </div>
      <!-- <span class="text-sm text-gray-600">{{ "24, Aug 2024" }}</span> -->
      <span class="text-sm text-gray-600">{{
        dayjs.tz(article.published_on).format("DD, MMM YYYY")
      }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Avatar } from "frappe-ui";
import { dayjs } from "@/dayjs";
import { Article, Author } from "@/types";
import { computed } from "vue";
import { ComputedRef } from "vue";

const props = defineProps<{
  article: Article;
  author: Author;
}>();

const articleSubTitle = computed(
  () =>
    props.article.subtitle ||
    "This article helps you understand the topic effectively."
);

const articleImg = computed(
  () => props.article.article_image || "/assets/helpdesk/desk/article.png"
);
</script>

<style scoped></style>
