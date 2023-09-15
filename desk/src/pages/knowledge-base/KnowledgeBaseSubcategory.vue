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
    <ListView :columns="columns" :resource="articles" doctype="HD Article">
      <template #title="{ data }">
        <div class="flex items-center gap-2">
          <IconFile class="h-4 w-4" />
          {{ data.title }}
        </div>
      </template>
      <template #status="{ data }">
        <Badge
          :theme="data.status === 'Published' ? 'green' : 'orange'"
          variant="subtle"
        >
          {{ data.status }}
        </Badge>
      </template>
      <template #emptyMessage>
        <EmptyMessage message="This sub category is empty" />
      </template>
    </ListView>
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
import { ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import {
  createDocumentResource,
  debounce,
  Badge,
  Button,
  Dialog,
  FormControl,
} from "frappe-ui";
import { AGENT_PORTAL_KNOWLEDGE_BASE_ARTICLE } from "@/router";
import { createListManager } from "@/composables/listManager";
import { useError } from "@/composables/error";
import { ListView } from "@/components";
import KnowledgeBaseCategoryHeader from "./KnowledgeBaseCategoryHeader.vue";
import EmptyMessage from "@/components/EmptyMessage.vue";
import IconEdit from "~icons/lucide/edit-3";
import IconFile from "~icons/lucide/file-text";
import IconPlus from "~icons/lucide/plus";

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

const articles = createListManager({
  doctype: "HD Article",
  filters: {
    category: props.subCategoryId,
  },
  auto: true,
  transform: (data) => {
    for (const d of data) {
      d.onClick = {
        name: AGENT_PORTAL_KNOWLEDGE_BASE_ARTICLE,
        params: {
          articleId: d.name,
        },
      };
    }
    return data;
  },
});

const columns = [
  {
    label: "Title",
    key: "title",
    width: "w-96",
  },
  {
    label: "Views",
    key: "views",
    width: "w-12",
  },
  {
    label: "Status",
    key: "status",
    width: "w-40",
  },
];

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
