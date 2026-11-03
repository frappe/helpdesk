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
        <p v-if="hasLinked" class="text-p-base text-ink-gray-7">
          {{ citedMessage }}
        </p>
      </div>
    </template>
    <template #actions>
      <div class="flex gap-2">
        <Button
          v-if="hasLinked"
          class="w-full"
          variant="subtle"
          :label="__('Archive linked')"
          :loading="deleteCategory.loading"
          @click="emit('confirm', true, true)"
        />
        <Button
          class="w-full"
          variant="solid"
          theme="red"
          :label="hasLinked ? __('Delete') : __('Confirm')"
          :disabled="!summary && !categoryDeleteSummary.error"
          :loading="deleteCategory.loading"
          @click="emit('confirm', deleteArticles, false)"
        />
      </div>
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
const emit = defineEmits<{
  confirm: [deleteArticles: boolean, archiveCited: boolean];
}>();
const showDialog = defineModel<boolean>();
const deleteArticles = ref(false);

const summary = computed(() => categoryDeleteSummary.data);
// articles that tickets link to: archive them or delete them too
const hasLinked = computed(
  () => deleteArticles.value && Boolean(summary.value?.cited)
);

watch(showDialog, (open) => {
  if (!open) return;
  categoryDeleteSummary.reset();
  categoryDeleteSummary.submit({ category: props.category });
});

const message = computed(() => {
  if (deleteArticles.value) {
    const subcategories = summary.value?.subcategories ?? 0;
    const articles = countLabel(
      summary.value?.articles ?? 0,
      __("1 article"),
      __("{0} articles")
    );
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
  countLabel(
    summary.value?.cited ?? 0,
    __(
      "1 article is linked to a ticket. Archive it to keep the link, or delete it and remove it from the ticket."
    ),
    __(
      "{0} articles are linked to tickets. Archive them to keep the links, or delete them and remove them from those tickets."
    )
  )
);
</script>
