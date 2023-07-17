<template>
  <div
    class="h-full space-y-2 border-r px-3.5 py-2.5"
    :style="{
      'min-width': '242px',
      'max-width': '242px',
    }"
  >
    <div class="flex items-center justify-between">
      <div class="text-sm font-medium text-gray-600">Categories</div>
      <Button
        theme="gray"
        variant="ghost"
        @click="showNewDialog = !showNewDialog"
      >
        <template #icon>
          <Icon icon="lucide:plus" class="h-4 w-4" />
        </template>
      </Button>
    </div>
    <div class="flex flex-col gap-1">
      <SidebarLink
        v-for="category in categories.data"
        :key="category.label"
        :icon="getIcon(category.icon)"
        :is-active="activeCategory === category.name"
        :label="category.category_name"
        @click="activeCategory = category.name"
      />
    </div>
    <Dialog v-model="showNewDialog" :options="dialogOptions">
      <template #body-content>
        <form @submit.prevent="newCategoryRes.submit">
          <div class="space-y-4">
            <div class="space-y-2">
              <div class="text-xs text-gray-700">Title</div>
              <div class="flex items-center gap-2">
                <Popover>
                  <template #target="{ togglePopover }">
                    <Button @click="togglePopover">
                      <template #icon>
                        <component :is="getIcon(newCategoryIcon)" />
                      </template>
                    </Button>
                  </template>
                  <template #body-main="{ togglePopover }">
                    <div class="grid grid-cols-6 gap-2 p-2">
                      <Button
                        v-for="icon in icons"
                        :key="icon"
                        class="place-self-center"
                        @click="
                          () => {
                            newCategoryIcon = icon;
                            togglePopover();
                          }
                        "
                      >
                        <template #icon>
                          <component :is="getIcon(icon)" />
                        </template>
                      </Button>
                    </div>
                  </template>
                </Popover>
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
            <Button
              class="w-full"
              label="Create"
              theme="gray"
              variant="solid"
            />
          </div>
        </form>
      </template>
    </Dialog>
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue";
import {
  createResource,
  createListResource,
  Button,
  Dialog,
  FormControl,
  Popover,
} from "frappe-ui";
import { storeToRefs } from "pinia";
import { Icon } from "@iconify/vue";
import SidebarLink from "@/components/SidebarLink.vue";
import { useKnowledgeBaseStore, icons } from "./data";
import { getIcon } from "./util";

const { activeCategory } = storeToRefs(useKnowledgeBaseStore());
const categories = createListResource({
  doctype: "HD Article Category",
  auto: true,
  fields: ["name", "category_name", "icon"],
  filters: {
    parent_category: "",
  },
});
const newCategoryName = ref("");
const newCategoryDescription = ref("");
const newCategoryIcon = ref("");
const showNewDialog = ref(false);
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
    categories.reload().then(() => (activeCategory.value = data.name));
  },
});
const dialogOptions = {
  title: "New category",
};
</script>
