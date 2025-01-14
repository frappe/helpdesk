<template>
  <div class="flex gap-5 flex-wrap wrap" v-if="!categories.loading">
    <CategoryFolder v-for="category in categories.data" :category="category" />
  </div>
</template>

<script setup lang="ts">
import CategoryFolder from "./CategoryFolder.vue";
import { createListResource } from "frappe-ui";

const categories = createListResource({
  doctype: "HD Article Category",
  fields: ["name", "category_name", "modified"],
  auto: true,
});
</script>

<style scoped></style>
