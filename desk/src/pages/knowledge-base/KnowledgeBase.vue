<template>
  <div class="flex flex-col">
    <LayoutHeader>
      <template #left-header>
        <div class="text-lg font-medium text-gray-900">Knowledge base</div>
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
      v-model="showDialog"
      v-model:title="category.title"
      @update="handleCategoryUpdate"
      @create="handleCategoryCreate"
    />
  </div>
</template>

<script setup lang="ts">
import { h, ref, reactive } from "vue";
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
} from "@/stores/knowledgeBase";

import LayoutHeader from "@/components/LayoutHeader.vue";
import ListViewBuilder from "@/components/ListViewBuilder.vue";
import CategoryModal from "@/components/knowledge-base/CategoryModal.vue";
import { createToast } from "@/utils";

const router = useRouter();

const showDialog = ref(false);
const category = reactive({
  title: "",
  id: "",
});
const _title = ref("");
const editTitle = ref(false);
const listViewRef = ref(null);

const headerOptions = [
  {
    label: "Category",
    icon: "folder",
    onClick: () => {
      resetState();
      editTitle.value = false;
      showDialog.value = true;
    },
  },
  {
    label: "Article",
    icon: "file",
    onClick: () => {
      router.push({ name: "NewArticle" });
      // router.push({
      //   name: "NewArticle",
      //   query: {
      //     category: "ABC",
      //   },
      // });
    },
  },
];

const groupByActions = [
  {
    label: "Add New Article",
    icon: "plus",
    onClick: (groupedRow) => {
      console.log("Add Article", groupedRow);
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
      showDialog.value = true;
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

function handleCategoryCreate() {
  console.log("Create", category.title);
  newCategory.submit(
    {
      category_name: category.title,
    },
    {
      onSuccess: () => {
        listViewRef.value.reload();
        showDialog.value = false;
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
    showDialog.value = false;
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
        showDialog.value = false;
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

function resetState() {
  category.title = "";
  category.id = "";
  _title.value = "";
}

const options = {
  doctype: "HD Article",
  view: {
    view_type: "group_by",
    group_by_field: "category",
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
          name: "file",
          class: "w-4 h-4",
        });
      },
    },
  },
  groupByActions,
};

usePageMeta(() => {
  return {
    title: "Knowledge base",
  };
});
</script>
