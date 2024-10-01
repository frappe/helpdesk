<template>
  <div
    class="flex flex-col p-5 px-10 overflow-scroll w-full"
    v-if="!categoryTreeResource.isLoading"
  >
    <!-- Top Section -->
    <section class="flex flex-col gap-3.5 mb-5">
      <h3 class="text-2xl font-semibold text-gray-800">
        {{ category.categoryName }}
      </h3>
      <FormControl
        type="text"
        class="w-full"
        placeholder="Search articles"
        size="md"
        v-model="category.search"
      />
    </section>
    <!-- Sub categories Section -->
    <section class="flex flex-col gap-3" v-if="!!category.subCategories.length">
      <h3 class="text-lg font-semibold text-gray-800">Sub-categories</h3>
      <!-- sub category card container-->
      <div class="flex gap-5 flex-wrap">
        <!-- sub category card -->
        <div
          v-for="subCategory in category.subCategories"
          class="border rounded px-3.5 py-3 cursor-pointer max-w-[220px] min-w-[220px]"
        >
          <h5 class="truncate text-lg">{{ subCategory["category_name"] }}</h5>
          <span class="text-sm text-gray-600">
            {{ subCategory.articles.length }} articles
          </span>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { reactive, watch } from "vue";
import { createResource, FormControl } from "frappe-ui";

const props = defineProps<{
  categoryId: string;
}>();

const category = reactive({
  categoryName: "",
  subCategories: [],
  articles: [],
  search: "",
});

const categoryTreeResource = createResource({
  url: "helpdesk.api.kbase.get_sub_categories_and_articles",
  name: props.categoryId,
  cache: ["category", props.categoryId],
  params: {
    category: props.categoryId,
  },
  auto: true,
  onSuccess: (categoryData) => {
    category.categoryName = categoryData["root_category"].category_name;
    category.subCategories = categoryData["sub_categories"];
    category.articles = categoryData["all_articles"];
  },
});

watch(
  async () => categoryTreeResource.data,
  async () => {
    const data = await categoryTreeResource.data;
    category.categoryName = data["root_category"].category_name;
    category.subCategories = data["sub_categories"];
    category.articles = data["all_articles"];
    return data;
  }
);

watch(
  () => props.categoryId,
  () => {
    categoryTreeResource.update({
      params: {
        category: props.categoryId,
      },
    });
    categoryTreeResource.reload().then((categoryData) => {
      category.categoryName = categoryData["root_category"].category_name;
      category.subCategories = categoryData["sub_categories"];
      category.articles = categoryData["all_articles"];
    });
  }
);
</script>

<style scoped></style>
