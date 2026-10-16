<template>
  <Dialog
    title="Merge with another category"
    @after-leave="
      () => {
        toCategory = null;
      }
    "
    v-model:open="showDialog"
  >
    <template #default>
      <p class="text-p-base text-ink-gray-8 mb-4">
        This will move all articles of the
        <span class="whitespace-nowrap font-semibold">{{ categoryTitle }}</span>
        category to the selected category. This change is irreversible!
      </p>
      <Link
        class="form-control"
        doctype="HD Article Category"
        placeholder="Select Category"
        v-model="toCategory"
        label="Category"
        :page-length="100"
      />
      <p v-if="joining.data" class="mt-3 text-p-sm text-ink-gray-7">
        {{
          __(
            "Articles in this category are visible to {0}, so merged articles will be too.",
            [visibleTo(joining.data)]
          )
        }}
      </p>
    </template>
    <template #actions>
      <Button
        class="w-full"
        variant="solid"
        label="Merge"
        @click="emit('merge', categoryId, toCategory)"
      />
    </template>
  </Dialog>
</template>
<script setup lang="ts">
import { ref } from "vue";
import { Dialog } from "frappe-ui";
import { Link } from "@/components";
import { useCategoryVisibility, visibleTo } from "@/stores/knowledgeBase";
defineProps<{
  categoryId: string;
  categoryTitle: string;
}>();
const emit = defineEmits(["merge"]);
const showDialog = defineModel<boolean>();

const toCategory = ref("");
const joining = useCategoryVisibility(toCategory);
</script>
