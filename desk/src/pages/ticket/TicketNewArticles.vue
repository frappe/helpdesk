<template>
  <div
    v-if="!isEmpty(articles.data)"
    class="rounded border bg-cyan-50 px-5 py-3 text-base"
  >
    <div class="mb-2 font-medium">
      Did you know? These articles might cover what you looking for!
    </div>
    <ul class="space-y-2">
      <li
        v-for="a in articles.data"
        :key="a.name"
        class="list-inside list-disc"
      >
        <RouterLink
          class="group cursor-pointer space-x-1 hover:text-gray-900"
          :to="{
            name: 'KBArticlePublic',
            params: {
              articleId: a.name,
            },
          }"
          target="_blank"
        >
          <span class="text-gray-800">
            {{ a.title }}
          </span>
          <span class="opacity-0 transition-all group-hover:opacity-100">
            &LongRightArrow;
          </span>
        </RouterLink>
      </li>
    </ul>
  </div>
</template>

<script setup lang="ts">
import { watch } from "vue";
import { createListResource } from "frappe-ui";
import { isEmpty } from "lodash";

interface P {
  search: string;
}

const props = defineProps<P>();
const articles = createListResource({
  doctype: "HD Article",
  auto: false,
  debounce: 500,
  pageLength: 5,
  fields: ["name", "title"],
});
watch(
  () => props.search,
  (search) => {
    if (search.length < 5) return;
    articles.update({
      filters: {
        title: ["like", `%${search}%`],
      },
    });
    articles.reload();
  }
);
</script>
