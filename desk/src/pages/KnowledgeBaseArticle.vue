<template>
  <div class="flex h-full flex-col overflow-hidden">
    <LayoutHeader>
      <template #left-header>
        <Breadcrumbs :items="breadcrumbs" />
      </template>
      <template #right-header v-if="!isCustomerPortal">
        <component
          :is="actionsComponent"
          :status="article.data?.status"
          @cancel="() => article.reload().then((editMode = !editMode))"
          @create="insertRes.submit"
          @delete="deleteRes.submit"
          @discard="router.push(backTo)"
          @save="updateContent"
          @toggle-edit-mode="editMode = !editMode"
          @toggle-status="toggleStatus"
        />
      </template>
    </LayoutHeader>
    <div class="overflow-auto mx-auto w-full max-w-4xl px-5">
      <div class="py-6">
        <TextEditor
          :content="textEditorContentWithIDs"
          :editable="editMode"
          :placeholder="placeholder"
          :extensions="[PreserveIds]"
          class="rounded"
          :class="{
            shadow: editMode,
            'p-4': editMode,
          }"
          editor-class="prose-f"
          @change="articleContent = $event"
        >
          <template #top v-if="!route.meta.public">
            <component
              :is="topComponent"
              v-model:title="articleTitle"
              v-bind="options__"
            />

            <TextEditorFixedMenu
              v-if="editMode"
              class="-ml-1"
              :buttons="textEditorMenuButtons"
            />
          </template>
        </TextEditor>
        <!-- <div
          v-else-if="!article.data && !editMode"
          class="text-gray-500 text-2xl font-semibold mb-5"
        >
          Article Not Found
        </div> -->
        <RouterLink
          v-if="route.meta.public"
          :to="{ name: CUSTOMER_PORTAL_NEW_TICKET }"
          class=""
        >
          <Button
            label="Still need help? Create a ticket"
            size="md"
            theme="gray"
            variant="solid"
            class="mt-5"
          >
            <template #suffix> &rightarrow; </template>
          </Button>
        </RouterLink>
      </div>
    </div>
  </div>
</template>
<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import { capture } from "@/telemetry";
import {
  createResource,
  createDocumentResource,
  debounce,
  Button,
  TextEditor,
  TextEditorFixedMenu,
  Breadcrumbs,
} from "frappe-ui";
import {
  AGENT_PORTAL_KNOWLEDGE_BASE_ARTICLE,
  AGENT_PORTAL_KNOWLEDGE_BASE_CATEGORY,
  AGENT_PORTAL_KNOWLEDGE_BASE_SUB_CATEGORY,
  CUSTOMER_PORTAL_NEW_TICKET,
} from "@/router";
import { createToast } from "@/utils";
import { useAuthStore } from "@/stores/auth";
import { useError } from "@/composables/error";

import { LayoutHeader, PageTitle } from "@/components";
import KnowledgeBaseArticleActionsEdit from "./knowledge-base/KnowledgeBaseArticleActionsEdit.vue";
import KnowledgeBaseArticleActionsNew from "./knowledge-base/KnowledgeBaseArticleActionsNew.vue";
import KnowledgeBaseArticleActionsView from "./knowledge-base/KnowledgeBaseArticleActionsView.vue";
import KnowledgeBaseArticleTopEdit from "./knowledge-base/KnowledgeBaseArticleTopEdit.vue";
import KnowledgeBaseArticleTopNew from "./knowledge-base/KnowledgeBaseArticleTopNew.vue";
import KnowledgeBaseArticleTopView from "./knowledge-base/KnowledgeBaseArticleTopView.vue";
import { Extension } from "@tiptap/core";

const props = defineProps({
  articleId: {
    type: String,
    required: true,
  },
});

onMounted(() => {
  setTimeout(() => {
    scrollToHeading();
  }, 100);
});

function scrollToHeading() {
  const articleHeading = window.location.hash;
  if (!articleHeading) return;
  const headingElement = document.querySelector(articleHeading);
  if (!headingElement) return;
  headingElement.scrollIntoView({ behavior: "smooth" });
}

const route = useRoute();
const router = useRouter();
const authStore = useAuthStore();
const isNew = props.articleId === "new";
const editMode = ref(isNew);
const categoryId = computed(() => router.currentRoute.value.query.category);
const subCategoryId = computed(
  () => router.currentRoute.value.query.subCategory
);

const isCustomerPortal = computed(() => route.meta.public);

const breadcrumbs = computed(() => {
  const agentPortalItems = [
    {
      label: options__.value.categoryName,
      route: {
        name: AGENT_PORTAL_KNOWLEDGE_BASE_CATEGORY,
        params: { categoryId: options__.value.categoryId },
      },
    },
  ];
  // if (options__.value.subCategoryId !== options__.value.categoryId) {
  agentPortalItems.push({
    label: options__.value.subCategoryName,
    route: {
      name: AGENT_PORTAL_KNOWLEDGE_BASE_SUB_CATEGORY,
      params: {
        categoryId: options__.value.categoryId,
        subCategoryId:
          options__.value.subCategoryId || options__.value.categoryId,
      },
    },
  });
  // }

  if (!isNew) {
    agentPortalItems.push({
      label: article.data?.title,
      route: {
        name: AGENT_PORTAL_KNOWLEDGE_BASE_ARTICLE,
        params: {
          articleId: article.data?.name,
        },
      },
    });
  }
  if (!isCustomerPortal.value) {
    return agentPortalItems;
  }
  const customerPortalItems = [
    {
      label: "Knowledge Base",
      route: {
        name: "KnowledgeBasePublicNew",
      },
    },
  ];
  if (options__.value.categoryId) {
    customerPortalItems.push({
      label: options__.value.categoryName,
      route: {
        name: "KnowledgeBasePublicNew",
        query: { category: options__.value.categoryId },
      },
    });
  }
  if (options__.value.subCategoryId) {
    customerPortalItems.push({
      label: options__.value.subCategoryName,
      route: {
        name: "KnowledgeBasePublicNew",
        query: {
          category: options__.value.categoryId,
          subCategory: options__.value.subCategoryId,
        },
      },
    });
  }

  return customerPortalItems;
});
const placeholder = computed(() =>
  editMode.value ? "Write something..." : "Content is empty"
);
const articleContent = ref("");
const articleTitle = ref("");

const actionsComponent = computed(() => {
  if (isNew) return KnowledgeBaseArticleActionsNew;
  if (editMode.value) return KnowledgeBaseArticleActionsEdit;
  return KnowledgeBaseArticleActionsView;
});

const topComponent = computed(() => {
  if (isNew) return KnowledgeBaseArticleTopNew;
  if (editMode.value) return KnowledgeBaseArticleTopEdit;
  return KnowledgeBaseArticleTopView;
});

const article = createResource({
  url: "helpdesk.helpdesk.doctype.hd_article.api.get_article",
  params: {
    name: props.articleId,
  },
  onSuccess(data) {
    articleTitle.value = data.title;
    capture("article_viewed", {
      data: {
        user: authStore.userId,
        article: data.name,
        title: data.title,
      },
    });
  },
  auto: !isNew,
});

const category = createDocumentResource({
  doctype: "HD Article Category",
  name: categoryId.value,
  auto: true,
});

const subCategory = createDocumentResource({
  doctype: "HD Article Category",
  name: subCategoryId.value,
  auto: subCategoryId.value !== categoryId.value ? true : false,
});

const options__ = computed(() => ({
  authorFullname: article.data?.author.full_name || authStore.userName,
  authorImage: article.data?.author.user_image || authStore.userImage,
  categoryId: categoryId.value,
  categoryName:
    article.data?.category.category_name || category?.doc?.category_name,
  creation: article.data?.creation,
  modified: article.data?.modified,
  status: article.data?.status,
  subCategoryId: subCategoryId.value,
  subCategoryName:
    article.data?.sub_category.category_name || subCategory?.doc?.category_name,
  title: article.data?.title,
}));

const insertRes = createResource({
  url: "frappe.client.insert",
  makeParams() {
    return {
      doc: {
        doctype: "HD Article",
        category: subCategoryId.value,
        title: articleTitle.value,
        content: articleContent.value,
      },
    };
  },
  validate(params) {
    if (!params.doc.title) throw "Title is required";
    if (!params.doc.content) throw "Content is required";
  },
  onSuccess(data) {
    router.push({
      name: AGENT_PORTAL_KNOWLEDGE_BASE_ARTICLE,
      params: {
        articleId: data.name,
      },
    });
  },
  onError: useError({ title: "Error creating article" }),
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
  onError: useError({ title: "Error updating article" }),
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
    fieldname: {
      content: articleContent.value,
      title: articleTitle.value,
    },
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

const backTo = computed(() => ({
  name: AGENT_PORTAL_KNOWLEDGE_BASE_SUB_CATEGORY,
  params: {
    categoryId: categoryId.value,
    subCategoryId: subCategoryId.value,
  },
}));

const textEditorMenuButtons = [
  "Paragraph",
  ["Heading 2", "Heading 3", "Heading 4", "Heading 5", "Heading 6"],
  "Separator",
  "Bold",
  "Italic",
  "Separator",
  "Bullet List",
  "Numbered List",
  "Separator",
  "Align Left",
  "Align Center",
  "Align Right",
  "FontColor",
  "Separator",
  "Image",
  "Video",
  "Link",
  "Blockquote",
  "Code",
  "Horizontal Rule",
  [
    "InsertTable",
    "AddColumnBefore",
    "AddColumnAfter",
    "DeleteColumn",
    "AddRowBefore",
    "AddRowAfter",
    "DeleteRow",
    "MergeCells",
    "SplitCell",
    "ToggleHeaderColumn",
    "ToggleHeaderRow",
    "ToggleHeaderCell",
    "DeleteTable",
  ],
];

// extension to preserve ids in html of headings
const PreserveIds: Extension = Extension.create({
  name: "preserveIds",
  addGlobalAttributes() {
    return [
      {
        types: ["heading"],
        attributes: {
          id: {
            default: null,
            parseHTML: (element) => element.getAttribute("id"),
            renderHTML: (attributes) => {
              if (!attributes.id) {
                return {};
              }
              return { id: attributes.id };
            },
          },
        },
      },
    ];
  },
});

const textEditorContentWithIDs = computed(() =>
  article.data?.content ? addLinksToHeadings(article.data?.content) : null
);

function addLinksToHeadings(content: string) {
  const parser = new DOMParser();
  const doc = parser.parseFromString(content, "text/html");
  const headings = doc.querySelectorAll("h2, h3, h4, h5, h6");
  headings.forEach((heading) => {
    const text = heading.textContent.trim();
    const id = text.replace(/[^a-z0-9]+/gi, "-").toLowerCase();
    heading.setAttribute("id", id);
  });
  return doc.body.innerHTML;
}
</script>
