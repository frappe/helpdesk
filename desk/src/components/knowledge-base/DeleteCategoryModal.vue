<template>
  <Dialog
    v-model:open="showDialog"
    :title="__('Delete category?')"
    @after-leave="deleteArticles = false"
  >
    <template #default>
      <div class="flex flex-col gap-3">
        <Checkbox
          v-model="deleteArticles"
          :label="__('Also delete articles')"
          :disabled="!summary"
        />
        <p class="text-p-base text-ink-gray-7">{{ message }}</p>
        <p
          v-if="deleteArticles && summary?.cited"
          class="text-p-base text-ink-gray-7"
        >
          {{
            __("{0} articles cited by tickets will be archived", [
              summary.cited,
            ])
          }}
        </p>
      </div>
    </template>
    <template #actions>
      <Button
        class="w-full"
        variant="solid"
        theme="red"
        :label="__('Confirm')"
        :disabled="!summary"
        :loading="deleteCategory.loading"
        @click="emit('confirm', deleteArticles)"
      />
    </template>
  </Dialog>
</template>

<script setup lang="ts">
import { computed, ref, watch } from "vue";
import { Button, Checkbox, Dialog } from "frappe-ui";
import { categoryDeleteSummary, deleteCategory } from "@/stores/knowledgeBase";
import { __ } from "@/translation";

const props = defineProps<{
  category: string;
  // A Subcategory's articles move to its parent, not General.
  isSubcategory?: boolean;
}>();
const emit = defineEmits<{ confirm: [deleteArticles: boolean] }>();
const showDialog = defineModel<boolean>();
const deleteArticles = ref(false);

const summary = computed(() => categoryDeleteSummary.data);

watch(showDialog, (open) => {
  if (!open) return;
  categoryDeleteSummary.reset();
  categoryDeleteSummary.submit({ category: props.category });
});

const message = computed(() => {
  if (deleteArticles.value) {
    return __("Deletes {0} subcategories and {1} articles", [
      summary.value?.subcategories ?? 0,
      summary.value?.articles ?? 0,
    ]);
  }
  return props.isSubcategory
    ? __("Articles in this subcategory will move to the parent category.")
    : __(
        "Subcategories will become top-level categories and articles will move to the General category."
      );
});
</script>
