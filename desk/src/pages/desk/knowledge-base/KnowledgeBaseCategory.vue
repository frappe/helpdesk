<template>
  <div class="grow px-5 py-3.5">
    <div class="mb-6 space-y-1">
      <div class="flex items-center justify-between">
        <div class="text-xl font-medium text-gray-900">
          {{ category.doc?.category_name }}
        </div>
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
      </div>
      <div
        class="text-base text-gray-700"
        :style="{
          width: '770px',
        }"
      >
        {{ category.doc?.description }}
      </div>
    </div>
    <div class="gap-5.5 grid grid-cols-3">
      <KnowledgeBaseCategoryCard
        v-for="c in subCategories.data"
        :key="c.name"
        class="w-full place-self-center"
        :title="c.category_name"
        :description="c.description"
        :article-count="c.count_article"
      />
    </div>
    <Dialog v-model="showEdit" :options="{ title: 'Edit Category' }">
      <template #body-content>
        <form @submit.prevent="saveCategory">
          <div class="space-y-4">
            <FormControl
              v-model="newCategoryName"
              :placeholder="category.doc.category_name"
              label="Name"
              type="text"
            />
            <FormControl
              v-model="newCategoryDescription"
              :placeholder="category.doc.description"
              label="Description"
              type="textarea"
            />
            <Button
              :disabled="!newCategoryName && !newCategoryDescription"
              class="w-full"
              label="Save"
              theme="gray"
              variant="solid"
            />
          </div>
        </form>
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
import { ref } from "vue";
import {
  createResource,
  createDocumentResource,
  debounce,
  Button,
  Dialog,
  FormControl,
} from "frappe-ui";
import { isEmpty } from "lodash";
import { createToast } from "@/utils/toasts";
import { createListManager } from "@/composables/listManager";
import KnowledgeBaseCategoryCard from "./KnowledgeBaseCategoryCard.vue";
import IconEdit from "~icons/lucide/edit-3";
import IconPlus from "~icons/lucide/plus";

const newSubCategoryName = ref("");
const newSubCategoryDescription = ref("");
const showNewSubCategory = ref(false);
const newCategoryName = ref("");
const newCategoryDescription = ref("");
const showEdit = ref(false);

const category = createDocumentResource({
  doctype: "HD Article Category",
  name: "dd01268bcc",
  auto: true,
  setValue: {
    onError(error) {
      createToast({
        title: "Error creating sub category",
        text: error.messages.join(", "),
        icon: "x",
        iconClasses: "text-red-500",
      });
    },
  },
});

const saveCategory = debounce(
  () =>
    category.setValue.submit({
      category_name: newCategoryName.value || category.doc.category_name,
      description: newCategoryDescription.value || category.doc.description,
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
  onError(error) {
    const msg = error.message ? error.message : error.messages.join(", ");
    createToast({
      title: "Error creating sub category",
      text: msg,
      icon: "x",
      iconClasses: "text-red-500",
    });
  },
});

const subCategories = createListManager({
  doctype: "HD Article Category",
  filters: {
    parent_category: "dd01268bcc",
  },
  auto: true,
});
</script>
