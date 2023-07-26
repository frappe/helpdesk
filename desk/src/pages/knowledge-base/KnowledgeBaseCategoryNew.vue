<template>
  <Dialog v-bind="attrs" :options="{ title: 'New category' }">
    <template #body-content>
      <form @submit.prevent="newCategoryRes.submit">
        <div class="space-y-4">
          <div class="space-y-2">
            <div class="text-xs text-gray-700">Title</div>
            <div class="flex items-center gap-2">
              <KnowledgeBaseIconSelector
                :icon="newCategoryIcon"
                @select="(icon) => (newCategoryIcon = icon)"
              />
              <FormControl
                v-model="newCategoryName"
                placeholder="A brief guide"
                type="text"
              />
            </div>
          </div>
          <div class="space-y-2">
            <div class="text-xs text-gray-700">Description</div>
            <FormControl
              v-model="newCategoryDescription"
              placeholder="A short description"
              type="textarea"
            />
          </div>
          <Button class="w-full" label="Create" theme="gray" variant="solid" />
        </div>
      </form>
    </template>
  </Dialog>
</template>

<script setup lang="ts">
import { ref, useAttrs } from "vue";
import { createResource, Button, Dialog, FormControl } from "frappe-ui";
import KnowledgeBaseIconSelector from "./KnowledgeBaseIconSelector.vue";

interface E {
  (event: "success", id: string): void;
}

const attrs = useAttrs();
const emit = defineEmits<E>();
const newCategoryName = ref("");
const newCategoryDescription = ref("");
const newCategoryIcon = ref("");
const newCategoryRes = createResource({
  url: "frappe.client.insert",
  makeParams() {
    return {
      doc: {
        doctype: "HD Article Category",
        category_name: newCategoryName.value,
        description: newCategoryDescription.value,
        icon: newCategoryIcon.value,
      },
    };
  },
  validate(params) {
    const requiredFields = ["category_name", "description", "icon"];
    for (const f of requiredFields) {
      if (params.doc[f]) return;
      const field = f.replace("_", " ").toUpperCase();
      return `${field} is required`;
    }
  },
  onSuccess(data) {
    emit("success", data.name);
  },
});
</script>
