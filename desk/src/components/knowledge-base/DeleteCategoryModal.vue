<template>
  <Dialog v-model:open="showDialog" :title="__('Delete category?')">
    <template #default>
      <div class="flex flex-col gap-3">
        <p class="text-p-base text-ink-gray-7">{{ message }}</p>
        <p v-if="summary?.subcategories" class="text-p-base text-ink-gray-7">
          {{
            __("Moving them also makes its subcategories top-level categories.")
          }}
        </p>
        <p v-if="summary?.cited" class="text-p-base text-ink-gray-7">
          {{ citedMessage(summary.cited) }}
        </p>
      </div>
    </template>
    <template #actions>
      <div class="flex w-full flex-col gap-2">
        <template v-if="hasContent">
          <Button
            variant="subtle"
            icon-left="lucide-folder-input"
            :label="
              isSubcategory
                ? __('Move articles to parent category')
                : __('Move articles to General')
            "
            :disabled="!ready || deleteCategory.loading"
            :loading="deleteCategory.loading && choice === 'move'"
            @click="confirm('move')"
          />
          <Button
            v-if="summary?.cited"
            variant="subtle"
            icon-left="lucide-archive"
            :label="__('Delete articles, archive linked')"
            :disabled="deleteCategory.loading"
            :loading="deleteCategory.loading && choice === 'archive'"
            @click="confirm('archive')"
          />
        </template>
        <Button
          variant="solid"
          theme="red"
          icon-left="lucide-trash-2"
          :label="deleteLabel"
          :disabled="!ready || deleteCategory.loading"
          :loading="deleteCategory.loading && choice === 'delete'"
          @click="confirm('delete')"
        />
      </div>
    </template>
  </Dialog>
</template>

<script setup lang="ts">
import { computed, ref, watch } from "vue";
import { Button, Dialog } from "frappe-ui";
import { citedMessage } from "@/utils";
import { categoryDeleteSummary, deleteCategory } from "@/stores/knowledgeBase";
import { __ } from "@/translation";

const props = defineProps<{
  category: string;
  title: string;
  // A Subcategory's articles move to its parent, not General.
  isSubcategory?: boolean;
}>();
const emit = defineEmits<{
  confirm: [deleteArticles: boolean, archiveLinked: boolean];
}>();
const showDialog = defineModel<boolean>();
const choice = ref<"move" | "archive" | "delete">();

const summary = computed(() => categoryDeleteSummary.data);
// a failed summary still lets the user choose
const ready = computed(
  () => Boolean(summary.value) || Boolean(categoryDeleteSummary.error)
);
// an empty category has nothing to move or keep
const hasContent = computed(
  () => !summary.value || summary.value.articles || summary.value.subcategories
);

watch(showDialog, (open) => {
  if (!open) return;
  categoryDeleteSummary.reset();
  categoryDeleteSummary.submit({ category: props.category });
});

const message = computed(() =>
  hasContent.value
    ? __("What should happen to the articles in {0}?", [props.title])
    : __("{0} has no articles.", [props.title])
);

const deleteLabel = computed(() => {
  if (!hasContent.value) return __("Delete category");
  return summary.value?.cited || summary.value?.subcategories
    ? __("Delete everything")
    : __("Delete articles");
});

function confirm(value: "move" | "archive" | "delete") {
  choice.value = value;
  emit("confirm", value !== "move", value === "archive");
}
</script>
