<template>
  <Dialog v-model:open="showDialog" title="Move To" :actions="actions">
    <template #default>
      <div class="flex flex-col flex-1">
        <Combobox
          class="w-full"
          v-model="category"
          :options="options"
          :placeholder="__('Select Category')"
        />
        <AnimatedNote :note="joiningNote" />
      </div>
    </template>
  </Dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch } from "vue";
import { Combobox, Dialog } from "frappe-ui";
import AnimatedNote from "./AnimatedNote.vue";
import { categoryOptions, useCategoryVisibility } from "@/stores/knowledgeBase";
import { __ } from "@/translation";

const emit = defineEmits(["move"]);
const showDialog = defineModel<boolean>();
const category = ref("");
const joining = useCategoryVisibility(category);
// A move only narrows access; Public needs no note.
const joiningNote = computed(
  () =>
    ({
      Customers: __(
        "Articles in this category are visible to customers only. Moved public articles will have the same visibility."
      ),
      Private: __(
        "Articles in this category are visible to agents only. Moved articles will have the same visibility."
      ),
    }[joining.data])
);

const props = defineProps<{
  excludeCategory?: string;
}>();

const options = computed(() =>
  (categoryOptions.data || []).map(({ value, label }) => ({ value, label }))
);
watch(showDialog, (open) => {
  if (open) categoryOptions.submit({ exclude: props.excludeCategory });
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
