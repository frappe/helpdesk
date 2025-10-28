<template>
  <div class="flex flex-col">
    <LayoutHeader>
      <template #left-header>
        <div class="text-lg font-medium text-gray-900">{{ tKnowledgeBase }}</div>
      </template>
      <template #right-header>
        <Dropdown :options="headerOptions">
          <Button :label="tAddNew" variant="solid">
            <template #prefix>
              <LucidePlus class="h-4 w-4" />
            </template>
          </Button>
        </Dropdown>
      </template>
    </LayoutHeader>
    <ListViewBuilder
      ref="listViewRef"
      :options="options"
      @row-click="(row) => $router.push(`kb/articles/${row}`)"
    />
    <CategoryModal
      :edit="editTitle"
      v-model="showCategoryModal"
      v-model:title="category.title"
      @update="handleCategoryUpdate"
      @create="handleCategoryCreate"
    />
    <MoveToCategoryModal v-model="moveToModal" @move="handleMoveToCategory" />
    <MergeCategoryModal
      :categoryTitle="category.title"
      :category-id="category.id"
      v-model="mergeModal"
      @merge="handleMergeCategory"
    />
  </div>
</template>

<script setup lang="ts">
import LayoutHeader from "@/components/LayoutHeader.vue";
import ListViewBuilder from "@/components/ListViewBuilder.vue";
import CategoryModal from "@/components/knowledge-base/CategoryModal.vue";
import MergeCategoryModal from "@/components/knowledge-base/MergeCategoryModal.vue";
import MoveToCategoryModal from "@/components/knowledge-base/MoveToCategoryModal.vue";
import { globalStore } from "@/stores/globalStore";
import {
  deleteArticles,
  deleteRes as deleteCategory,
  mergeCategory,
  moveToCategory,
  newCategory,
  updateCategoryTitle,
} from "@/stores/knowledgeBase";
import { capture } from "@/telemetry";
import { Error } from "@/types";
import { copyToClipboard } from "@/utils";
import {
  Badge,
  Button,
  Dropdown,
  FeatherIcon,
  createResource,
  toast,
  usePageMeta,
} from "frappe-ui";
import { computed, h, onMounted, reactive, ref } from "vue";
import { useRouter } from "vue-router";
import LucideMerge from "~icons/lucide/merge";
import { useTranslation } from "@/composables/useTranslation";

const router = useRouter();
const { $dialog } = globalStore();

// Reactive translations
const tKnowledgeBase = useTranslation("Knowledge Base");
const tAddNew = useTranslation("Add new");
const tCategory = useTranslation("Category");
const tArticle = useTranslation("Article");
const tGeneral = useTranslation("General");
const tAddNewArticle = useTranslation("Add New Article");
const tEditTitle = useTranslation("Edit Title");
const tMerge = useTranslation("Merge");
const tShare = useTranslation("Share");
const tDelete = useTranslation("Delete");
const tMoveTo = useTranslation("Move To");
const tConfirm = useTranslation("Confirm");
const tDeleteArticlesQuestion = useTranslation("Delete articles?");
const tDeleteArticlesMessage = useTranslation("Are you sure you want to delete these articles?");
const tArticlesMoved = useTranslation("Articles moved");
const tCategoryCreated = useTranslation("Category created");
const tCategoryUpdated = useTranslation("Category updated");
const tDeleteCategoryQuestion = useTranslation("Delete category?");
const tDeleteCategoryMessage = useTranslation("All articles from this category will move to General category.");
const tCategoryDeleted = useTranslation("Category deleted");
const tArticlesDeleted = useTranslation("Articles deleted");
const tCategoryMerged = useTranslation("Category merged");
const tPublished = useTranslation("Published");
const tDraft = useTranslation("Draft");
const tArchived = useTranslation("Archived");

const category = reactive({
  title: "",
  id: "",
});

const _title = ref("");
const listViewRef = ref(null);
const editTitle = ref(false);

// modals state
const showCategoryModal = ref(false);
const moveToModal = ref(false);
const mergeModal = ref(false);

const generalCategory = createResource({
  url: "helpdesk.api.knowledge_base.get_general_category",
  auto: true,
  cache: ["GeneralCategory"],
});

const headerOptions = computed(() => [
  {
    label: tCategory.value,
    icon: "folder",
    onClick: () => {
      resetState();
      editTitle.value = false;
      showCategoryModal.value = true;
    },
  },
  {
    label: tArticle.value,
    icon: "file-text",
    onClick: () => {
      router.push({
        name: "NewArticle",
        params: {
          id: generalCategory.data,
        },
        query: {
          title: tGeneral.value,
        },
      });
    },
  },
]);

const groupByActions = computed(() => [
  {
    label: tAddNewArticle.value,
    icon: "plus",
    onClick: (groupedRow) => {
      router.push({
        name: "NewArticle",
        params: {
          id: groupedRow.group.value,
        },
        query: {
          title: groupedRow.group.label,
        },
      });
    },
  },
  {
    label: tEditTitle.value,
    icon: "edit",
    onClick: (groupedRow) => {
      editTitle.value = true;
      showCategoryModal.value = true;
      category.title = groupedRow.group.label;
      category.id = groupedRow.group.value;
      _title.value = groupedRow.group.label;
    },
  },
  {
    label: tMerge.value,
    icon: LucideMerge,
    onClick: (groupedRow) => {
      mergeModal.value = true;
      category.title = groupedRow.group.label;
      category.id = groupedRow.group.value;
    },
  },
  {
    label: tShare.value,
    icon: "link",
    onClick: async ({ group }) => {
      const { label, value } = group;
      const url = new URL(window.location.href);
      url.pathname = `/helpdesk/kb-public/${value}`;
      await copyToClipboard(
        url.toString(),
        `Category <u>'${label}'</u> link copied to clipboard`
      );
    },
  },
  {
    label: tDelete.value,
    icon: "trash-2",
    onClick: (groupedRow) => {
      handleCategoryDelete(groupedRow);
    },
  },
]);

const listSelections = ref(new Set());
const selectBannerActions = computed(() => [
  {
    label: tMoveTo.value,
    icon: "corner-up-right",
    onClick: (selections: Set<string>) => {
      listSelections.value = new Set(selections);
      moveToModal.value = true;
    },
  },
  {
    label: tDelete.value,
    icon: "trash-2",
    onClick: (selections: Set<string>) => {
      listSelections.value = selections;
      $dialog({
        title: tDeleteArticlesQuestion.value,
        message: tDeleteArticlesMessage.value,
        actions: [
          {
            label: tConfirm.value,
            variant: "solid",
            onClick({ close }) {
              handleDeleteArticles();
              close();
            },
          },
        ],
      });
    },
  },
]);

function handleMoveToCategory(category: string) {
  moveToCategory.submit(
    {
      category,
      articles: Array.from(listSelections.value),
    },
    {
      onSuccess: () => {
        moveToModal.value = false;
        listViewRef.value?.reload();
        listViewRef.value?.unselectAll();
        listSelections.value.clear();
        toast.success(tArticlesMoved.value);
      },
      onError: (error: Error) => {
        const title = error?.messages?.[0] || error.message;
        toast.error(title);
        moveToModal.value = false;
      },
    }
  );
}

function handleCategoryCreate() {
  newCategory.submit(
    {
      title: category.title,
    },
    {
      onSuccess: (data: any) => {
        listViewRef.value.reload();
        showCategoryModal.value = false;
        router.push({
          name: "Article",
          params: {
            articleId: data.article,
          },
          query: {
            category: data.category,
            title: category.title,
            isEdit: 1,
          },
        });
        toast.success(tCategoryCreated.value);
        capture("category_created", {
          data: {
            category: category.title,
          },
        });
        resetState();
      },
      onError: (error: string) => {
        toast.error(error);
      },
    }
  );
}

function handleCategoryUpdate() {
  // if same title do nothing
  if (category.title === _title.value) {
    showCategoryModal.value = false;
    editTitle.value = false;
    return;
  }
  updateCategoryTitle.submit(
    {
      doctype: "HD Article Category",
      name: category.id,
      fieldname: "category_name",
      value: category.title,
    },
    {
      onSuccess: () => {
        listViewRef.value.reload();
        showCategoryModal.value = false;
        editTitle.value = false;

        toast.success(tCategoryUpdated.value);
        resetState();
      },
      onError: (error: string) => {
        toast.error(error);
      },
    }
  );
}

function handleCategoryDelete(groupedRow) {
  $dialog({
    title: tDeleteCategoryQuestion.value,
    message: tDeleteCategoryMessage.value,
    actions: [
      {
        label: tConfirm.value,
        variant: "solid",
        onClick(close: Function) {
          deleteCategory.submit(
            {
              doctype: "HD Article Category",
              name: groupedRow.group.value,
            },
            {
              onSuccess: () => {
                toast.success(tCategoryDeleted.value);
                listViewRef.value.reload();
              },
            }
          );
          close();
        },
      },
    ],
  });
}

function handleDeleteArticles() {
  deleteArticles.submit(
    {
      articles: Array.from(listSelections.value),
    },
    {
      onSuccess: () => {
        listViewRef.value?.reload();
        listViewRef.value?.unselectAll();
        listSelections.value?.clear();
        toast.success(tArticlesDeleted.value);
      },
    }
  );
}

function handleMergeCategory(source: string, target: string) {
  mergeCategory.submit(
    {
      source,
      target,
    },
    {
      onSuccess: () => {
        listViewRef.value.reload();
        toast.success(tCategoryMerged.value);
        mergeModal.value = false;
        resetState();
      },
      onError: (error: Error) => {
        const title = error?.messages?.[0] || error.message;
        toast.error(title);
      },
    }
  );
}

function resetState() {
  category.title = "";
  category.id = "";
  _title.value = "";
}

const options = computed(() => {
  return {
    doctype: "HD Article",
    selectable: true,
    view: {
      view_type: "group_by",
      group_by_field: "category",
      label_doc: "HD Article Category",
      label_field: "category_name",
    },
    columnConfig: {
      title: {
        prefix: () => {
          return h(FeatherIcon, {
            name: "file-text",
            class: "h-4 w-4 flex-shrink-0 text-ink-gray-6",
          });
        },
      },
      status: {
        custom: ({ item }) => {
          return h(Badge, {
            ...statusMap.value[item],
          });
        },
      },
    },
    rowRoute: {
      name: "Article",
      prop: "articleId",
    },
    groupByActions: groupByActions.value,
    showSelectBanner: true,
    selectBannerActions: selectBannerActions.value,
    default_page_length: 100,
  };
});

const statusMap = computed(() => ({
  Published: {
    label: tPublished.value,
    theme: "green",
  },
  Draft: {
    label: tDraft.value,
    theme: "orange",
  },
  Archived: {
    label: tArchived.value,
    theme: "gray",
  },
}));

onMounted(() => {
  capture("kb_agent_page_viewed");
});

usePageMeta(() => {
  return {
    title: tKnowledgeBase.value,
  };
});
</script>
