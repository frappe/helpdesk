<template>
  <Dialog
    :options="{
      title: 'Merge with another category',
    }"
    @after-leave="
      () => {
        toCategory = null;
      }
    "
    v-model="showDialog"
  >
    <template #body-content>
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
defineProps<{
  categoryId: string;
  categoryTitle: string;
}>();
const emit = defineEmits(["merge"]);
const showDialog = defineModel<boolean>();

const toCategory = ref("");
</script>
