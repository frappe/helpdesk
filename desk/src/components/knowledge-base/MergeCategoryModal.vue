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
import { computed, ref } from "vue";
import { Dialog } from "frappe-ui";
import { Link } from "@/components";
import AnimatedNote from "./AnimatedNote.vue";
import { useCategoryVisibility } from "@/stores/knowledgeBase";
import { __ } from "@/translation";
defineProps<{
  categoryId: string;
  categoryTitle: string;
}>();
const emit = defineEmits(["merge"]);
const showDialog = defineModel<boolean>();

const toCategory = ref("");
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
