<template>
  <Dialog v-model="showDialog" :options="{ title: 'Move To', actions }">
    <template #body-content>
      <div class="flex flex-col flex-1 gap-3">
        <Link
          ref="linkRef"
          class="form-control"
          doctype="HD Article Category"
          placeholder="Select Category"
          v-model="category"
          label="Category"
          :filters="defaultFilters"
          :page-length="100"
        />
      </div>
    </template>
  </Dialog>
</template>

<script setup lang="ts">
import { ref, watch, nextTick, computed } from "vue";
import { Dialog } from "frappe-ui";
import { Link } from "frappe-ui/frappe";
import { Filter } from "@/types";

const emit = defineEmits(["move"]);
const showDialog = defineModel<boolean>();
const category = ref("");
const linkRef = ref(null);

const props = defineProps<{
  excludeCategory?: string;
}>();

const defaultFilters = computed(() => {
  if (!props.excludeCategory) return {};

  return {
    name: ["!=", props.excludeCategory],
  };
});
watch(showDialog, async (val) => {
  if (!val) return;
  await nextTick();
  setTimeout(() => {
    linkRef.value?.$el?.querySelector("input")?.focus();
  }, 300);
});

const actions = [
  {
    label: "Move",
    variant: "solid",
    onClick: () => {
      emit("move", category.value);
      category.value = "";
    },
  },
];
</script>
