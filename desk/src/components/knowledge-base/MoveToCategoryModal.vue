<template>
  <Dialog v-model="showDialog" :options="{ title: 'Move To', actions }">
    <template #body-content>
      <div class="flex flex-col flex-1 gap-3">
        <Link
          class="form-control"
          doctype="HD Article Category"
          placeholder="Select Category"
          v-model="category"
          label="Category"
          :page-length="100"
        />
      </div>
    </template>
  </Dialog>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { Dialog } from "frappe-ui";
import { Link } from "@/components";

const emit = defineEmits(["move"]);
const showDialog = defineModel<boolean>();

const category = ref("");

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
