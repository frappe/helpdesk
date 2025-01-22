<template>
  <div
    v-if="!isEmpty(articles.data) && query.length > 2"
    class="rounded border p-4 text-base"
  >
    <div class="mb-2 font-medium pl-2" v-if="!hideViewAll">
      These articles may already cover what you are looking for
      <RouterLink
        class="group cursor-pointer space-x-1 hover:text-gray-900"
        :to="{
          name: 'CustomerKnowledgeBase',
        }"
        target="_blank"
      >
        <span class="text-xs underline">(View All)</span>
      </RouterLink>
    </div>
    <dl
      class="mx-auto w-full flex flex-col gap-2"
      v-if="articles.data.length > 0"
    >
      <div
        v-for="a in articles.data"
        :key="a.id"
        class="rounded-md border-2 p-2 border-hidden hover:bg-surface-gray-2"
      >
        <RouterLink
          class="group cursor-pointer hover:text-gray-900 flex flex-col gap-1"
          :to="{
            name: 'ArticlePublic',
            params: {
              articleId: a.name.split('#')[0],
            },
            hash: `#${a.name.split('#')[1]}`,
          }"
          @click="handleSearchArticleClick(a)"
          target="_blank"
        >
          <dt class="font-base">{{ a.subject }} - {{ a.headings }}</dt>
          <!-- eslint-disable-next-line vue/no-v-html -->
          <dd
            class="font-base text-p-sm text-gray-600 line-clamp-1"
            v-html="a.description"
          ></dd>
        </RouterLink>
      </div>
    </dl>
  </div>
  <div
    v-else-if="
      !articles.loading && articles.data?.length === 0 && query.length > 2
    "
    class="flex flex-col items-center justify-center h-[240px] gap-2 rounded border"
  >
    <Icon icon="heroicons-outline:search" class="h-8 w-8 text-gray-400" />
    <div class="flex items-center flex-col justify-center">
      <p class="font-base">No answers found</p>
      <span class="font-base text-p-sm text-gray-600 text-center"
        >Rephrase the question and try again with some keywords</span
      >
    </div>
  </div>
  <div
    v-else-if="articles.loading"
    class="flex flex-col items-center justify-center h-[240px] gap-2 rounded border"
  >
    <Icon icon="heroicons-outline:search" class="h-8 w-8 text-gray-400" />
    <div class="flex items-center flex-col justify-center">
      <p class="font-base">Searching...</p>
      <span class="font-base text-p-sm text-gray-600 text-center"
        >Please wait while we search for the answers</span
      >
    </div>
  </div>
</template>

<script setup lang="ts">
import { watch } from "vue";
import { createResource } from "frappe-ui";
import { isEmpty } from "lodash";
import { Icon } from "@iconify/vue";
import { capture } from "@/telemetry";
interface P {
  query: string;
  hideViewAll?: boolean;
}

const { query = "", hideViewAll = false } = defineProps<P>();
const articles = createResource({
  url: "helpdesk.api.article.search",
  debounce: 500,
  auto: false,
});
watch(
  () => query,
  (query) => {
    if (query.length < 3) return;
    articles.update({
      params: {
        query: query,
      },
    });
    articles.reload();
  }
);

function handleSearchArticleClick(article) {
  capture("kb_customer_search_article_clicked", {
    data: {
      article: article.subject,
    },
  });
}
</script>
