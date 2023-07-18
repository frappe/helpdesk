<template>
  <div class="flex flex-col overflow-hidden">
    <TopBar :back-to="backTo" :title="article.data?.title" class="sticky top-0">
      <template #right>
        <component
          :is="actionsComponent"
          :status="article.data?.status"
          @cancel="() => article.reload().then((editMode = !editMode))"
          @delete="deleteRes.submit"
          @save="updateContent"
          @toggle-edit-mode="editMode = !editMode"
          @toggle-status="toggleStatus"
        />
      </template>
    </TopBar>
    <div class="overflow-auto">
      <div class="m-auto my-6 rounded-xl" :style="containerStyle">
        <TextEditor
          :bubble-menu="true"
          :content="article.data?.content"
          :editable="editMode"
          :floating-menu="true"
          :placeholder="editMode ? 'Write something...' : 'Content is empty'"
          class="rounded-xl px-6 py-4"
          editor-class="prose prose-sm prose-img:rounded prose-img:border max-w-none my-4"
          @change="article.data.content = $event"
        >
          <template #top>
            <component
              :is="topComponent"
              :author-fullname="article.data?.author.full_name"
              :author-image="article.data?.author.user_image"
              :category-name="article.data?.category.category_name"
              :creation="article.data?.creation"
              :dislikes="article.data?.not_helpful"
              :likes="article.data?.helpful"
              :modified="article.data?.modified"
              :status="article.data?.status"
              :sub-category-name="article.data?.sub_category.category_name"
              :title="article.data?.title"
            />
          </template>
        </TextEditor>
      </div>
    </div>
  </div>
</template>
<script setup lang="ts">
import { computed, ref } from "vue";
import { useRouter } from "vue-router";
import { createResource, debounce, TextEditor } from "frappe-ui";
import { AGENT_PORTAL_KNOWLEDGE_BASE_SUB_CATEGORY } from "@/router";
import { createToast } from "@/utils/toasts";
import TopBar from "@/components/TopBar.vue";
import KnowledgeBaseArticleActionsEdit from "./KnowledgeBaseArticleActionsEdit.vue";
import KnowledgeBaseArticleActionsView from "./KnowledgeBaseArticleActionsView.vue";
import KnowledgeBaseArticleTopEdit from "./KnowledgeBaseArticleTopEdit.vue";
import KnowledgeBaseArticleTopView from "./KnowledgeBaseArticleTopView.vue";

const props = defineProps({
  articleId: {
    type: String,
    required: true,
  },
});

const router = useRouter();
const editMode = ref(false);
const actionsComponent = computed(() => {
  if (editMode.value) return KnowledgeBaseArticleActionsEdit;
  return KnowledgeBaseArticleActionsView;
});
const topComponent = computed(() => {
  if (editMode.value) return KnowledgeBaseArticleTopEdit;
  return KnowledgeBaseArticleTopView;
});
const article = createResource({
  url: "helpdesk.helpdesk.doctype.hd_article.api.get_article",
  params: {
    name: props.articleId,
  },
  auto: true,
});

const setValueRes = createResource({
  url: "frappe.client.set_value",
  onSuccess() {
    article.reload();
    createToast({
      title: "Article updated",
      icon: "check",
      iconClasses: "text-green-500",
    });
  },
  onError(error) {
    const msg = error.messages.join(", ");
    createToast({
      title: "Error updating article",
      text: msg,
      icon: "x",
      iconClasses: "text-red-500",
    });
  },
});

const deleteRes = createResource({
  url: "frappe.client.delete",
  makeParams() {
    return {
      doctype: "HD Article",
      name: props.articleId,
    };
  },
  onSuccess() {
    router.replace(backTo.value);
  },
});

const updateContent = debounce(() => {
  setValueRes.submit({
    doctype: "HD Article",
    name: article.data.name,
    fieldname: "content",
    value: article.data.content,
  });
}, 300);

const toggleStatus = debounce(() => {
  const status = article.data.status === "Published" ? "Draft" : "Published";
  setValueRes.submit({
    doctype: "HD Article",
    name: article.data.name,
    fieldname: "status",
    value: status,
  });
}, 300);

const containerStyle = computed(() => ({
  width: "790px",
  "box-shadow": editMode.value
    ? "0px 1px 2px 0px rgba(0, 0, 0, 0.1), 0px 0px 1px 0px rgba(0, 0, 0, 0.45)"
    : "",
}));

const backTo = computed(() => ({
  name: AGENT_PORTAL_KNOWLEDGE_BASE_SUB_CATEGORY,
  params: {
    categoryId: article.data?.category.name,
    subCategoryId: article.data?.sub_category.name,
  },
}));
</script>
