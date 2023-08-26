<template>
  <div class="flex grow flex-col">
    <KnowledgeBaseCategoryHeader
      :title="category.doc?.category_name"
      :description="category.doc?.description"
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
            @click="showNewSubCategory = !showNewSubCategory"
          >
            <template #prefix>
              <IconPlus class="h-4 w-4" />
            </template>
          </Button>
        </div>
      </template>
    </KnowledgeBaseCategoryHeader>
    <EmptyMessage
      v-if="isEmpty(subCategories.data)"
      message="This category is empty"
    />
    <div v-else class="gap-4.5 grid grid-cols-3 px-5">
      <HCard
        v-for="c in subCategories.data"
        :key="c.name"
        :description="c.description"
        :title="c.category_name"
        class="w-full place-self-center"
        @click="toSubcategory(c.name)"
      >
        <template #bottom>
          <div class="text-base text-gray-600">
            {{ c.count_article ? c.count_article : "No" }}
            {{ c.count_article > 1 ? "articles" : "article" }}
          </div>
        </template>
      </HCard>
    </div>
    <Dialog v-model="showEdit" :options="{ title: 'Edit' }">
      <template #body-content>
        <div class="space-y-4">
          <div class="space-y-2">
            <div class="text-xs text-gray-700">Title</div>
            <div class="flex items-center gap-2">
              <KnowledgeBaseIconSelector
                :icon="newCategoryIcon || category.doc?.icon"
                @select="(icon) => (newCategoryIcon = icon)"
              />
              <FormControl
                v-model="category.doc.category_name"
                placeholder="A brief guide"
                type="text"
              />
            </div>
          </div>
          <div class="space-y-2">
            <div class="text-xs text-gray-700">Description</div>
            <FormControl
              v-model="category.doc.description"
              placeholder="A short description"
              type="textarea"
            />
          </div>
          <Button
            class="w-full"
            label="Save"
            theme="gray"
            variant="solid"
            @click="saveCategory"
          />
        </div>
      </template>
    </Dialog>
    <Dialog
      v-model="showNewSubCategory"
      :options="{ title: 'New Sub category' }"
    >
      <template #body-content>
        <form @submit.prevent="newSubCategory.submit">
          <div class="space-y-4">
            <FormControl
              v-model="newSubCategoryName"
              type="text"
              label="Name"
              placeholder="Name"
            />
            <FormControl
              v-model="newSubCategoryDescription"
              type="textarea"
              label="Description"
              placeholder="Description"
            />
            <Button
              :disabled="isEmpty(newSubCategoryName)"
              class="w-full"
              label="Create"
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
import { ref, toRef } from "vue";
import { useRouter } from "vue-router";
import {
  createResource,
  createDocumentResource,
  debounce,
  Button as Button,
  Dialog,
  FormControl,
} from "frappe-ui";
import { isEmpty } from "lodash";
import { AGENT_PORTAL_KNOWLEDGE_BASE_SUB_CATEGORY } from "@/router";
import { createToast } from "@/utils";
import { createListManager } from "@/composables/listManager";
import { useError } from "@/composables/error";
import { HCard } from "@/components";
import KnowledgeBaseCategoryHeader from "./KnowledgeBaseCategoryHeader.vue";
import KnowledgeBaseIconSelector from "./KnowledgeBaseIconSelector.vue";
import EmptyMessage from "@/components/EmptyMessage.vue";
import IconEdit from "~icons/lucide/edit-3";
import IconPlus from "~icons/lucide/plus";

const props = defineProps({
  categoryId: {
    type: String,
    required: true,
  },
});

const router = useRouter();
const categoryId = toRef(props, "categoryId");
const newSubCategoryName = ref("");
const newSubCategoryDescription = ref("");
const showNewSubCategory = ref(false);
const newCategoryName = ref("");
const newCategoryDescription = ref("");
const newCategoryIcon = ref("");
const showEdit = ref(false);

const category = createDocumentResource({
  doctype: "HD Article Category",
  name: categoryId.value,
  auto: true,
  setValue: {
    onSuccess() {
      createToast({
        title: "Category updated",
        icon: "check",
        iconClasses: "text-green-500",
      });
    },
    onError: useError({ title: "Error updating category" }),
  },
});

const saveCategory = debounce(
  () =>
    category.setValue.submit({
      category_name: newCategoryName.value || category.doc.category_name,
      description: newCategoryDescription.value || category.doc.description,
      icon: newCategoryIcon.value || category.doc.icon,
    }),
  500
);

const newSubCategory = createResource({
  url: "frappe.client.insert",
  debounce: 500,
  makeParams() {
    return {
      doc: {
        doctype: "HD Article Category",
        category_name: newSubCategoryName.value,
        description: newSubCategoryDescription.value,
        parent_category: category.doc?.name,
      },
    };
  },
  validate(params) {
    if (isEmpty(params.doc.category_name)) {
      return "Category name is required";
    }
  },
  onSuccess() {
    showNewSubCategory.value = false;
    subCategories.reload();
  },
  onError: useError({ title: "Error creating sub category" }),
});

const subCategories = createListManager({
  doctype: "HD Article Category",
  filters: {
    parent_category: categoryId.value,
  },
  auto: true,
});

function toSubcategory(subCategoryId: string) {
  router.push({
    name: AGENT_PORTAL_KNOWLEDGE_BASE_SUB_CATEGORY,
    params: {
      subCategoryId,
    },
  });
}
</script>
