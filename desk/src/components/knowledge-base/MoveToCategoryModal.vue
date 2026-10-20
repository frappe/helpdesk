<template>
  <Dialog v-model:open="showDialog" title="Move To" :actions="actions">
    <template #default>
      <div class="flex flex-col flex-1">
        <Link
          ref="linkRef"
          class="w-full"
          doctype="HD Article Category"
          placeholder="Select Category"
          :search-placeholder="__('Search')"
          v-model="category"
          label="Category"
          :filters="defaultFilters"
          :page-length="100"
        />
        <!-- The note loads after a pick: the space opens, then the text rises in. -->
        <div
          class="grid transition-[grid-template-rows] duration-300 ease-[cubic-bezier(0.2,0.8,0.2,1)] motion-reduce:transition-none"
          :class="joiningNote ? 'grid-rows-[1fr]' : 'grid-rows-[0fr]'"
          aria-live="polite"
        >
          <div class="overflow-hidden">
            <p
              class="pt-3 text-p-sm text-ink-gray-7 transition-[opacity,transform,filter] ease-out motion-reduce:transition-none"
              :class="
                joiningNote
                  ? 'duration-300 delay-100'
                  : 'translate-y-1 opacity-0 blur-[2px] duration-150'
              "
            >
              {{ shownNote }}
            </p>
          </div>
        </div>
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

// Keeps the text while the note collapses.
const shownNote = ref("");
watch(joiningNote, (note) => note && (shownNote.value = note));

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
