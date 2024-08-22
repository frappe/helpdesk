<template>
  <div
    v-if="!isEmpty(articles.data) && search.length > 2"
    class="rounded border bg-cyan-50 px-5 py-3 text-base"
  >
    <div class="mb-2 font-medium">
      These articles may already cover what you are looking for
      <RouterLink
        class="group cursor-pointer space-x-1 hover:text-gray-900"
        :to="{
          name: 'KBHome',
        }"
        target="_blank"
      >
        <span class="text-xs">(View All)</span>
      </RouterLink>
    </div>
    <dl class="space-y-2">
      <div
        v-for="a in articles.data"
        :key="a.id"
        class="focus:ring-cyan-30 rounded-md border-2 border-hidden p-4 hover:bg-cyan-100 focus:outline-none focus:ring active:bg-cyan-50"
      >
        <RouterLink
          class="group cursor-pointer space-x-1 hover:text-gray-900"
          :to="{
            name: 'KBArticlePublic',
            params: {
              articleId: a.name.split('#')[0],
            },
            hash: `#${a.name.split('#')[1]}`,
          }"
          target="_blank"
        >
          <dt class="font-semibold">{{ a.subject }} - {{ a.headings }}</dt>
          <!-- eslint-disable-next-line vue/no-v-html -->
          <dd class="font-light" v-html="a.description"></dd>
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
  search: string;
}

const props = defineProps<P>();
const articles = createResource({
  url: "helpdesk.api.article.search",
  debounce: 500,
  auto: false,
});
watch(
  () => props.search,
  (search) => {
    if (search.length < 3) return;
    articles.update({
      params: {
        query: search,
      },
    });
    articles.reload();
  }
);
</script>
