<template>
  <div>
    <LayoutHeader>
      <template #left-header>
        <div class="flex gap-1 items-center">
          <Breadcrumbs :items="breadcrumbs" />
          <span> - </span>
          <Badge
            :label="article.data?.status"
            :theme="article.data?.status === 'Draft' ? 'red' : 'green'"
          />
        </div>
      </template>
      <template #right-header>
        <Button label="Edit" iconLeft="edit" />
        <Button
          variant="solid"
          :label="article.data?.status === 'Draft' ? 'Publish' : 'Unpublish'"
          :iconLeft="article.data?.status !== 'Published' && 'globe'"
          @click="toggleStatus()"
        />
      </template>
    </LayoutHeader>
    <div class="pt-6 mx-auto w-full max-w-4xl px-5" v-if="!article.loading">
      {{ article.data }}
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { Breadcrumbs, debounce, createResource, Badge } from "frappe-ui";
import LayoutHeader from "@/components/LayoutHeader.vue";
import { updateArticle } from "@/stores/article";
const props = defineProps({
  articleId: {
    type: String,
    required: true,
  },
});

const article = createResource({
  url: "helpdesk.helpdesk.doctype.hd_article.api.get_article2",
  params: {
    name: props.articleId,
  },
  auto: true,
});

const toggleStatus = debounce(() => {
  const status = article.data?.status === "Published" ? "Draft" : "Published";
  updateArticle.submit(
    {
      doctype: "HD Article",
      name: article.data.name,
      fieldname: "status",
      value: status,
    },
    {
      onSuccess: () => {
        article.reload();
      },
    }
  );
}, 300);

const breadcrumbs = computed(() => {
  const items = [
    {
      label: "Knowledge Base",
      route: { name: "AgentKnowledgeBase" },
    },
  ];
  if (article.data?.title) {
    items.push({
      label: article.data?.title,
      route: { name: "Article" },
    });
  }
  return items;
});
</script>

<style scoped></style>
