<template>
  <div class="flex flex-col p-5 px-10">
    <h3 class="text-xl font-semibold text-gray-800">
      {{ JSON.stringify(categoryTree, null, 4) }}
    </h3>
  </div>
</template>

<script setup lang="ts">
import { createListResource, createResource } from "frappe-ui";
import { ref } from "vue";
import { watch } from "vue";

const props = defineProps<{
  categoryId: string;
}>();

const categoryTree = ref(null);

const categoryTreeResource = createResource({
  url: "helpdesk.api.kbase.get_sub_categories_and_articles",
  name: props.categoryId,
  cache: ["category", props.categoryId],
  params: {
    category: props.categoryId,
  },
  onSuccess: (data) => {
    categoryTree.value = data;
  },
  auto: true,
});

watch(
  () => props.categoryId,
  () => {
    categoryTreeResource.update({
      params: {
        category: props.categoryId,
      },
    });
    categoryTreeResource.reload();
  }
);
</script>

<style scoped></style>
