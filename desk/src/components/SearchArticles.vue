<template>
  <div
    v-if="!isEmpty(articles.data) && query.length > 2"
    class="rounded border bg-cyan-50 px-5 py-3 text-base"
  >
    <div class="mb-2 font-medium px-4" v-if="!hideViewAll">
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
    <dl>
      <div
        v-for="a in articles.data"
        :key="a.id"
        class="focus:ring-cyan-30 rounded-md border-2 border-hidden p-4 hover:bg-cyan-100 focus:outline-none focus:ring active:bg-cyan-50"
      >
        <RouterLink
          class="group cursor-pointer hover:text-gray-900 flex flex-col gap-2"
          :to="{
            name: 'ArticlePublic',
            params: {
              articleId: a.name.split('#')[0],
            },
            hash: `#${a.name.split('#')[1]}`,
          }"
          target="_blank"
        >
          <dt class="font-semibold">{{ a.subject }} - {{ a.headings }}</dt>
          <!-- eslint-disable-next-line vue/no-v-html -->
          <dd class="font-light text-p-sm" v-html="a.description"></dd>
        </RouterLink>
      </div>
    </dl>
  </div>
</template>

<script setup lang="ts">
import { watch } from "vue";
import { createResource } from "frappe-ui";
import { isEmpty } from "lodash";

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
</script>
