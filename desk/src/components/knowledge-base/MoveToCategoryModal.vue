<template>
  <Dialog v-model:open="showDialog" title="Move To" :actions="actions">
    <template #default>
      <div class="flex flex-col flex-1 gap-3">
        <Link
          ref="linkRef"
          class="w-full"
          doctype="HD Article Category"
          placeholder="Select Category"
          v-model="category"
          label="Category"
          :filters="defaultFilters"
          :page-length="100"
        />
        <p v-if="joiningNote" class="text-p-sm text-ink-gray-7">
          {{ joiningNote }}
        </p>
      </div>
    </template>
  </Dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch, nextTick } from "vue";
import { Dialog } from "frappe-ui";
import Link from "@/components/frappe-ui/Link.vue";
import { useCategoryVisibility } from "@/stores/knowledgeBase";
import { __ } from "@/translation";

const emit = defineEmits(["move"]);
const showDialog = defineModel<boolean>();
const category = ref("");
const linkRef = ref(null);
const joining = useCategoryVisibility(category);
// A move only narrows access; Public needs no note.
const joiningNote = computed(
  () =>
    ({
      Customers: __(
        "Articles in this category are visible to customers only, so moved public articles will be too."
      ),
      Private: __(
        "Articles in this category are visible to agents only, so moved articles will be too."
      ),
    }[joining.data])
);

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
    linkRef.value?.$el?.querySelector("button")?.click();
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
