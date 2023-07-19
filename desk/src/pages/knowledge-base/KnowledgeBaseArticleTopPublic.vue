<template>
  <div class="mb-8 flex items-center gap-1.5">
    <RouterLink :to="{ name: KB_PUBLIC }">
      <Icon icon="lucide:home" class="h-4 w-4 text-gray-800" />
    </RouterLink>
    <Icon icon="lucide:chevron-right" class="h-4 w-4 text-gray-600" />
    <div
      class="cursor-pointer text-base font-medium text-gray-800"
      @click="toSubCategory"
    >
      {{ subCategoryName }}
    </div>
  </div>
  <div class="border-b pb-3">
    <div class="text-3xl font-semibold text-gray-900">
      {{ title }}
    </div>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from "vue-router";
import { KB_PUBLIC, KB_PUBLIC_CATEGORY } from "@/router";
import { Icon } from "@iconify/vue";
import { toRefs } from "vue";

const props = defineProps({
  subCategoryName: {
    type: String,
    required: true,
  },
  subCategoryId: {
    type: String,
    required: true,
  },
  title: {
    type: String,
    required: true,
  },
});

const router = useRouter();
const { subCategoryId } = toRefs(props);

function toSubCategory() {
  router.push({
    name: KB_PUBLIC_CATEGORY,
    params: {
      categoryId: subCategoryId.value,
    },
  });
}
</script>
