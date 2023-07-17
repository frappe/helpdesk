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
        :article-count="c.count_article"
        :description="c.description"
        :title="c.category_name"
        class="w-full place-self-center"
        @click="toSubcategory(c.name)"
      />
    </div>
    <Dialog v-model="showEdit" :options="{ title: 'Edit' }">
      <template #body-content>
        <form @submit.prevent="saveCategory">
          <div class="space-y-4">
            <div class="space-y-2">
              <div class="text-xs text-gray-700">Title</div>
              <div class="flex items-center gap-2">
                <Popover>
                  <template #target="{ togglePopover }">
                    <Button @click="togglePopover">
                      <template #icon>
                        <component
                          :is="getIcon(newCategoryIcon || category.doc?.icon)"
                        />
                      </template>
                    </Button>
                  </template>
                  <template #body-main="{ togglePopover }">
                    <div class="grid grid-cols-6 gap-2 p-2">
                      <Button
                        v-for="icon in icons"
                        :key="icon"
                        class="place-self-center"
                        @click="
                          () => {
                            category.doc.icon = icon;
                            togglePopover();
                          }
                        "
                      >
                        <template #icon>
                          <component :is="getIcon(icon)" />
                        </template>
                      </Button>
                    </div>
                  </template>
                </Popover>
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
            <Button class="w-full" label="Save" theme="gray" variant="solid" />
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
import { onUnmounted, ref } from "vue";
import { useRouter } from "vue-router";
import { storeToRefs } from "pinia";
import {
  createResource,
  createDocumentResource,
  debounce,
  Button as Button,
  Dialog,
  FormControl,
  Popover,
} from "frappe-ui";
import { isEmpty } from "lodash";
import { AGENT_PORTAL_KNOWLEDGE_BASE_CATEGORY } from "@/router";
import { createToast } from "@/utils/toasts";
import { createListManager } from "@/composables/listManager";
import KnowledgeBaseCategoryCard from "./KnowledgeBaseCategoryCard.vue";
import { useKnowledgeBaseStore, icons } from "./data";
import { getIcon } from "./util";
import IconEdit from "~icons/lucide/edit-3";
import IconPlus from "~icons/lucide/plus";

const props = defineProps({
  categoryId: {
    type: String,
    required: true,
  },
});

const router = useRouter();
const { activeCategory } = storeToRefs(useKnowledgeBaseStore());
const newSubCategoryName = ref("");
const newSubCategoryDescription = ref("");
const showNewSubCategory = ref(false);
const newCategoryName = ref("");
const newCategoryDescription = ref("");
const newCategoryIcon = ref("");
const showEdit = ref(false);

const category = createDocumentResource({
  doctype: "HD Article Category",
  name: props.categoryId,
  auto: true,
  onSuccess(data) {
    activeCategory.value = data.name;
  },
  setValue: {
    onSuccess() {
      createToast({
        title: "Article updated",
        icon: "check",
        iconClasses: "text-green-500",
      });
    },
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
    parent_category: props.categoryId,
  },
  auto: true,
});

onUnmounted(() => (activeCategory.value = ""));

function toSubcategory(subCategoryId: string) {
  router.push({
    name: AGENT_PORTAL_KNOWLEDGE_BASE_CATEGORY,
    params: {
      subCategoryId,
    },
  });
}
</script>
