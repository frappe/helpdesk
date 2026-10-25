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
        label="Merge"
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
  (categoryOptions.data || []).map(({ value, label }) => ({ value, label }))
);
watch(showDialog, (open) => {
  if (open) categoryOptions.submit({ exclude: props.categoryId });
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
