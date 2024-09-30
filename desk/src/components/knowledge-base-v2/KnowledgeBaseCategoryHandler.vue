<template>
  <div class="flex flex-col p-5 px-10">
    <h3 class="text-xl font-semibold text-gray-800">
      {{ categoryName }}
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

const categoryName = ref("");

const categoryResource = createResource({
  url: "helpdesk.api.kbase.get_category",
  name: props.categoryId,
  cache: ["category", props.categoryId],
  params: {
    category: props.categoryId,
  },
  onSuccess: (data) => {
    categoryName.value = data.category_name ?? data.name;
  },
  auto: true,
});

const subCategories = createListResource({
  doctype: "HD Article Category",
  name: props.categoryId,
  cache: ["category", props.categoryId],
  fields: ["name", "category_name", "icon", "parent_category"],
  filters: {
    parent_category: props.categoryId,
  },
  auto: true,
});
watch(
  () => props.categoryId,
  () => {
    categoryResource.update({
      params: {
        category: props.categoryId,
      },
    });

    subCategories.update({
      params: { name: props.categoryId },
    });

    categoryResource.reload();
    subCategories.reload();
  }
);
</script>

<style scoped></style>
