<template>
  <div class="flex flex-col">
    <LayoutHeader>
      <template #left-header>
        <div class="text-lg font-medium text-gray-900">Knowledge Base</div>
      </template>
      <template #right-header>
        <Dropdown :options="headerOptions">
          <Button label="Add new" variant="solid">
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
  </div>
</template>

<script setup lang="ts">
import { h, ref, reactive, computed } from "vue";
import {
  usePageMeta,
  FeatherIcon,
  Button,
  confirmDialog,
  Dropdown,
} from "frappe-ui";
import { useRouter } from "vue-router";
import {
  updateCategoryTitle,
  deleteCategory,
  newCategory,
  moveToCategory,
  deleteArticles,
} from "@/stores/knowledgeBase";
import LayoutHeader from "@/components/LayoutHeader.vue";
import ListViewBuilder from "@/components/ListViewBuilder.vue";
import CategoryModal from "@/components/knowledge-base/CategoryModal.vue";
import MoveToCategoryModal from "@/components/knowledge-base/MoveToCategoryModal.vue";
import { createToast } from "@/utils";

const router = useRouter();

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

const headerOptions = [
  {
    label: "Category",
    icon: "folder",
    onClick: () => {
      resetState();
      editTitle.value = false;
      showCategoryModal.value = true;
    },
  },
  {
    label: "Article",
    icon: "file-text",
    onClick: () => {
      router.push({ name: "NewArticle" });
    },
  },
];

const groupByActions = [
  {
    label: "Add New Article",
    icon: "plus",
    onClick: (groupedRow) => {
      router.push({
        name: "NewArticle",
        query: {
          category: groupedRow.group.value,
          title: groupedRow.group.label,
        },
      });
    },
  },
  {
    label: "Edit Title",
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
    label: "Delete",
    icon: "trash-2",
    onClick: (groupedRow) => {
      handleCategoryDelete(groupedRow);
    },
  },
];
const listSelections = ref(new Set());
const showSelectBanner = ref(true);
const selectBannerActions = [
  {
    label: "Move To",
    icon: "corner-up-right",
    onClick: (selections: Set<string>) => {
      listSelections.value = selections;
      moveToModal.value = true;
    },
  },
  {
    label: "Delete",
    icon: "trash-2",
    onClick: (selections: Set<string>) => {
      listSelections.value = selections;
      confirmDialog({
        title: "Delete articles?",
        message: `Are you sure you want to delete these articles?`,
        onConfirm: ({ hideDialog }: { hideDialog: Function }) => {
          handleDeleteArticles();
          hideDialog();
        },
      });
    },
  },
];

function handleMoveToCategory(category: string) {
  moveToCategory.submit(
    {
      category,
      articles: Array.from(listSelections.value),
    },
    {
      onSuccess: () => {
        listViewRef.value.reload();
        moveToModal.value = false;
        listSelections.value.clear();
        createToast({
          title: "Articles moved successfully",
          icon: "check",
          iconClasses: "text-green-600",
        });
      },
      onError: (error: string) => {
        createToast({
          title: error,
          icon: "x",
          iconClasses: "text-red-600",
        });
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
        createToast({
          title: "Category Created Successfully",
          icon: "check",
          iconClasses: "text-green-600",
        });
        resetState();
      },
      onError: (error: string) => {
        createToast({
          title: error,
          icon: "x",
          iconClasses: "text-red-600",
        });
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
        createToast({
          title: "Category Updated Successfully",
          icon: "check",
          iconClasses: "text-green-600",
        });

        resetState();
      },
      onError: (error: string) => {
        createToast({
          title: error,
          icon: "x",
          iconClasses: "text-red-600",
        });
      },
    }
  );
}

function handleCategoryDelete(groupedRow) {
  confirmDialog({
    title: "Delete category?",
    message: `All articles from this category will be uncatagorized.`,
    onConfirm: ({ hideDialog }: { hideDialog: Function }) => {
      deleteCategory.submit(
        {
          name: groupedRow.group.value,
        },
        {
          onSuccess: () => {
            createToast({
              title: "Article deleted successfully",
              icon: "check",
              iconClasses: "text-green-600",
            });
            listViewRef.value.reload();
          },
        }
      );
      hideDialog();
    },
  });
}

function handleDeleteArticles() {
  deleteArticles.submit(
    {
      articles: Array.from(listSelections.value),
    },
    {
      onSuccess: () => {
        listViewRef.value.reload();
        listSelections.value.clear();
        createToast({
          title: "Articles deleted successfully",
          icon: "check",
          iconClasses: "text-green-600",
        });
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
    view: {
      view_type: "group_by",
      group_by_field: "category",
      label_doc: "HD Article Category",
      label_field: "category_name",
    },
    statusMap: {
      Published: {
        label: "Published",
        theme: "green",
      },
      Draft: {
        label: "Draft",
        theme: "orange",
      },
      Archived: {
        label: "Archived",
        theme: "gray",
      },
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
    },
    groupByActions,
    showSelectBanner: showSelectBanner.value,
    selectBannerActions,
  };
});

usePageMeta(() => {
  return {
    title: "Knowledge Base",
  };
});
</script>
