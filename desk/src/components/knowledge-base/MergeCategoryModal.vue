<template>
  <Dialog :title="__('Merge with another category')" v-model:open="showDialog">
    <template #default>
      <p class="text-p-base text-ink-gray-8 mb-4">
        {{
          __(
            "Moves the articles and subcategories of {0} to the category you pick. You can't undo this.",
            [categoryTitle]
          )
        }}
      </p>
      <Combobox
        class="w-full"
        v-model="toCategory"
        :options="options"
        :placeholder="__('Select Category')"
      />
      <AnimatedNote :note="joiningNote" />
    </template>
    <template #actions>
      <Button
        class="w-full"
        variant="solid"
        :label="__('Merge')"
        @click="emit('merge', categoryId, toCategory)"
      />
    </template>
  </Dialog>
</template>
<script setup lang="ts">
import { computed, ref, watch } from "vue";
import { Combobox, Dialog } from "frappe-ui";
import AnimatedNote from "./AnimatedNote.vue";
import { categoryOptions, useCategoryVisibility } from "@/stores/knowledgeBase";
import { __ } from "@/translation";
const props = defineProps<{
  categoryId: string;
  categoryTitle: string;
}>();
const emit = defineEmits(["merge"]);
const showDialog = defineModel<boolean>();

const toCategory = ref("");
const options = computed(() =>
  (categoryOptions.data || [])
    .filter(({ value }) => value !== props.categoryId)
    .map(({ value, label }) => ({ value, label }))
);
watch(showDialog, (open) => {
  if (!open) return;
  // a pick made before a cancel must not survive
  toCategory.value = "";
  // shared with other dialogs: drop their list before it shows here
  categoryOptions.reset();
  categoryOptions.submit();
});
const joining = useCategoryVisibility(toCategory);
// A merge only narrows access; Public needs no note.
const joiningNote = computed(
  () =>
    ({
      Customers: __(
        "Articles in this category are visible to customers only. Merged public articles will have the same visibility."
      ),
      Private: __(
        "Articles in this category are visible to agents only. Merged articles will have the same visibility."
      ),
    }[joining.data])
);
</script>
