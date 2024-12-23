<template>
  <div class="flex grow flex-col">
    <KnowledgeBaseCategoryHeader
      :title="subCategory.doc?.category_name"
      :description="subCategory.doc?.description"
    >
      <template #right>
        <div class="space-x-2">
          <Button
            label="Edit"
            theme="gray"
            variant="outline"
            @click="showEdit = !showEdit"
          >
            <template #prefix>
              <IconEdit class="h-4 w-4" />
            </template>
          </Button>
          <Button
            label="Add new"
            theme="gray"
            variant="solid"
            @click="toNewArticle"
          >
            <template #prefix>
              <IconPlus class="h-4 w-4" />
            </template>
          </Button>
        </div>
      </template>
    </KnowledgeBaseCategoryHeader>
    <ListViewBuilder
      :options="options"
      @row-click="handleClick"
      @empty-state-action="toNewArticle"
    />
    <Dialog v-model="showEdit" :options="{ title: 'Edit' }">
      <template #body-content>
        <form @submit.prevent="saveSubCategory">
          <div class="space-y-4">
            <FormControl
              v-model="newSubCategoryName"
              :placeholder="subCategory.doc.category_name"
              label="Name"
              type="text"
            />
            <FormControl
              v-model="newSubCategoryDescription"
              :placeholder="subCategory.doc.description"
              label="Description"
              type="textarea"
            />
            <Button
              :disabled="!newSubCategoryName && !newSubCategoryDescription"
              class="w-full"
              label="Save"
              theme="gray"
              variant="solid"
            />
          </div>
        </form>
      </template>
    </Dialog>
  </div>
</template>
<script setup lang="ts">
import { ref, h } from "vue";
import { useRoute, useRouter } from "vue-router";
import { useUserStore } from "@/stores/user";
import {
  createDocumentResource,
  debounce,
  Button,
  Dialog,
  FormControl,
  Avatar,
} from "frappe-ui";
import { AGENT_PORTAL_KNOWLEDGE_BASE_ARTICLE } from "@/router";
import { useError } from "@/composables/error";
import KnowledgeBaseCategoryHeader from "./KnowledgeBaseCategoryHeader.vue";
import IconEdit from "~icons/lucide/edit-3";
import IconPlus from "~icons/lucide/plus";
import ListViewBuilder from "@/components/ListViewBuilder.vue";
const { getUser } = useUserStore();
const props = defineProps({
  subCategoryId: {
    type: String,
    required: true,
  },
});

const router = useRouter();
const route = useRoute();
const newSubCategoryName = ref("");
const newSubCategoryDescription = ref("");
const showEdit = ref(false);

const subCategory = createDocumentResource({
  doctype: "HD Article Category",
  name: props.subCategoryId,
  auto: true,
  setValue: {
    onError: useError({ title: "Error creating sub category" }),
  },
});

const saveSubCategory = debounce(
  () =>
    subCategory.setValue.submit({
      category_name: newSubCategoryName.value || subCategory.doc.category_name,
      description:
        newSubCategoryDescription.value || subCategory.doc.description,
    }),
  500
);

const options = {
  doctype: "HD Article",
  defaultFilters: {
    category: ["=", props.subCategoryId],
    status: ["!=", "Archived"],
  },
  columnConfig: {
    author: {
      prefix: ({ row }) => {
        return h(Avatar, {
          shape: "circle",
          image: getUser(row.author)?.user_image,
          label: row.author,
          size: "sm",
        });
      },
    },
  },
  statusMap: {
    Published: {
      label: "Published",
      theme: "green",
    },
    Draft: {
      label: "Draft",
      theme: "gray",
    },
  },
  emptyState: {
    title: "No Articles Found",
  },
  hideViewControls: true,
  listViewSelection: false,
};

function handleClick(id: string) {
  router.push({
    name: AGENT_PORTAL_KNOWLEDGE_BASE_ARTICLE,
    params: {
      articleId: id,
    },
    query: {
      category: route.params.categoryId,
      subCategory: route.params.subCategoryId,
    },
  });
}

function toNewArticle() {
  router.push({
    name: AGENT_PORTAL_KNOWLEDGE_BASE_ARTICLE,
    params: {
      articleId: "new",
    },
    query: {
      category: route.params.categoryId,
      subCategory: route.params.subCategoryId,
    },
  });
}
</script>
