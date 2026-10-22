<template>
  <div class="flex flex-col gap-3">
    <div class="flex items-start justify-between gap-4">
      <div class="flex min-w-0 flex-col">
        <h3 class="text-base-medium text-ink-gray-8">
          {{ __("Pinned categories") }}
        </h3>
        <span class="mt-1 text-base leading-5 text-ink-gray-6">
          {{
            __(
              "Pinned categories will appear first on your knowledge base home page, in this order."
            )
          }}
        </span>
      </div>
      <Button class="shrink-0" :label="__('Customize')" @click="open = true" />
    </div>
    <div
      v-if="pinned.length"
      class="rounded-5 border border-outline-gray-2 px-1"
    >
      <div
        v-for="(name, index) in pinned"
        :key="name"
        class="border-b border-outline-gray-1 py-1 last:border-b-0"
      >
        <div
          class="group flex h-11 items-center gap-2.5 rounded-4 pl-2 pr-1.5 hover:bg-surface-gray-1 sm:h-10"
        >
          <span
            :class="byName[name]?.icon || 'lucide-folder'"
            class="size-4 shrink-0 text-ink-gray-6"
          />
          <span class="min-w-0 flex-1 truncate text-base text-ink-gray-8">
            {{ labelOf(name) }}
          </span>
          <CategoryAccessBadge :access="byName[name]?.access" />
          <Dropdown align="end" :options="rowOptions(index)">
            <Button
              variant="ghost"
              icon="lucide-more-horizontal"
              :label="__('Options for {0}', [labelOf(name)])"
            />
          </Dropdown>
        </div>
      </div>
    </div>
    <!-- A row's height, so the first pin shifts nothing below. -->
    <div v-else class="rounded-5 border border-outline-gray-2 px-1 py-1">
      <div
        class="flex min-h-11 items-center justify-center px-3 text-center text-p-base text-ink-gray-6 sm:min-h-10"
      >
        {{
          __(
            "Nothing pinned yet. The home page will list all categories alphabetically."
          )
        }}
      </div>
    </div>
    <PinnedCategoriesDialog
      v-model:open="open"
      :categories="categories"
      :pinned="pinned"
      :save="save"
    />
  </div>
</template>

<script setup lang="ts">
import { __ } from "../translation";
import { Button, Dropdown } from "frappe-ui";
import { computed, ref } from "vue";
import CategoryAccessBadge from "./CategoryAccessBadge.vue";
import PinnedCategoriesDialog from "./PinnedCategoriesDialog.vue";

type Category = {
  label: string;
  value: string;
  icon: string;
  access?: string;
};

const props = defineProps<{
  categories: Category[];
  pinned: string[];
  // The Customize dialog saves at once; resolves true on success.
  save: (pinned: string[]) => Promise<boolean>;
}>();

// Row menu edits wait for the form's Save.
const emit = defineEmits<{ "update:pinned": [pinned: string[]] }>();

const open = ref(false);

const byName = computed(() =>
  Object.fromEntries(props.categories.map((row) => [row.value, row]))
);

function labelOf(name: string) {
  return byName.value[name]?.label || name;
}

function moveTo(name: string, index: number) {
  const next = props.pinned.filter((row) => row !== name);
  next.splice(index, 0, name);
  emit("update:pinned", next);
}

function rowOptions(index: number) {
  const name = props.pinned[index];
  return [
    {
      label: __("Move up"),
      icon: "lucide-arrow-up",
      disabled: index === 0,
      onClick: () => moveTo(name, index - 1),
    },
    {
      label: __("Move down"),
      icon: "lucide-arrow-down",
      disabled: index === props.pinned.length - 1,
      onClick: () => moveTo(name, index + 1),
    },
    {
      label: __("Unpin"),
      icon: "lucide-pin-off",
      onClick: () =>
        emit(
          "update:pinned",
          props.pinned.filter((row) => row !== name)
        ),
    },
  ];
}
</script>
