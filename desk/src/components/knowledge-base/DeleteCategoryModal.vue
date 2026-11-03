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
          {{ citedMessage }}
        </p>
      </div>
    </template>
    <template #actions>
      <Button
        class="w-full"
        variant="solid"
        theme="red"
        :label="__('Confirm')"
        :disabled="!summary && !categoryDeleteSummary.error"
        :loading="deleteCategory.loading"
        @click="emit('confirm', deleteArticles)"
      />
    </template>
  </Dialog>
</template>

<script setup lang="ts">
import { computed, ref, watch } from "vue";
import { Button, Checkbox, Dialog } from "frappe-ui";
import { countLabel } from "@helpdesk/shared/utils";
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
    const subcategories = summary.value?.subcategories ?? 0;
    // cited ones are archived, not deleted
    const deleted =
      (summary.value?.articles ?? 0) - (summary.value?.cited ?? 0);
    const articles = countLabel(deleted, __("1 article"), __("{0} articles"));
    return subcategories
      ? __("Deletes {0} and {1}", [
          countLabel(
            subcategories,
            __("1 subcategory"),
            __("{0} subcategories")
          ),
          articles,
        ])
      : __("Deletes {0}", [articles]);
  }
  if (props.isSubcategory) {
    return __("Articles in this subcategory will move to the parent category.");
  }
  return summary.value?.subcategories
    ? __(
        "Subcategories will become top-level categories and articles will move to the General category."
      )
    : __("Articles will move to the General category.");
});

const citedMessage = computed(() =>
  summary.value?.cited === 1
    ? __("1 article cited by tickets will be archived")
    : __("{0} articles cited by tickets will be archived", [
        summary.value?.cited,
      ])
);
</script>
