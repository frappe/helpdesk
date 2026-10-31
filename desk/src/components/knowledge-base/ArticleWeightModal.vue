<template>
  <Dialog
    v-model:open="open"
    :title="title"
    :actions="[{ label: __('Save'), variant: 'solid', onClick: save }]"
  >
    <template #default>
      <div class="flex flex-col gap-4">
        <FormControl
          v-model="weight"
          type="number"
          min="0"
          :label="__('Weight')"
          :description="
            __(
              'A higher weight lists first in its category. Leave 0 to keep the usual order, newest first.'
            )
          "
          @keydown.enter="save"
        />
        <div v-if="preview.length" class="flex flex-col gap-1.5">
          <div class="text-base-medium text-ink-gray-8">
            {{ __("Order customers will see") }}
          </div>
          <ol
            class="max-h-64 overflow-y-auto rounded-5 border border-outline-gray-2 p-1"
          >
            <li
              v-for="(row, index) in preview"
              :key="row.name"
              :aria-current="selected.has(row.name) || undefined"
              class="flex h-8 items-center gap-2 rounded-4 px-2 text-base"
              :class="
                selected.has(row.name)
                  ? 'bg-surface-gray-3 text-ink-gray-9'
                  : 'text-ink-gray-7'
              "
            >
              <span class="w-5 shrink-0 text-right text-p-sm text-ink-gray-5">
                {{ index + 1 }}
              </span>
              <span class="min-w-0 flex-1 truncate">{{ row.title }}</span>
              <span
                v-if="row.weight"
                class="shrink-0 text-p-sm text-ink-gray-5"
              >
                {{ __("Weight {0}", [row.weight]) }}
              </span>
            </li>
          </ol>
        </div>
      </div>
    </template>
  </Dialog>
</template>

<script setup lang="ts">
import { __ } from "@/translation";
import { createResource, Dialog, FormControl } from "frappe-ui";
import { computed, ref, watch } from "vue";

const props = defineProps<{
  articles: string[];
  // Previews the category's order; none when the articles span categories.
  category?: string;
  // The current weight, for one article.
  initialWeight?: number;
}>();

const emit = defineEmits<{ save: [weight: number] }>();

const open = defineModel<boolean>({ required: true });
const weight = ref<number | string>(0);
const cleanWeight = computed(() => Math.max(0, Number(weight.value) || 0));

const title = computed(() =>
  props.articles.length > 1
    ? __("Set weight for {0} articles", [props.articles.length])
    : __("Set weight")
);

// Published and not Private: what customers see, in the portal's order.
const siblings = createResource({
  url: "frappe.client.get_list",
  makeParams: () => ({
    doctype: "HD Article",
    filters: {
      category: props.category,
      status: "Published",
      visibility: ["!=", "Private"],
    },
    fields: ["name", "title", "weight", "published_on"],
    limit_page_length: 0,
  }),
});

watch(open, (value) => {
  if (!value) return;
  weight.value = props.initialWeight || 0;
  if (props.category) siblings.fetch();
  else siblings.data = null;
});

const selected = computed(() => new Set(props.articles));

// Re-sorts as the weight changes; ties go newest first, as the portal lists them.
const preview = computed(() =>
  (siblings.data || [])
    .map((row) => ({
      ...row,
      weight: selected.value.has(row.name) ? cleanWeight.value : row.weight,
    }))
    .sort(
      (a, b) =>
        b.weight - a.weight ||
        (b.published_on || "").localeCompare(a.published_on || "")
    )
);

function save() {
  open.value = false;
  emit("save", cleanWeight.value);
}
</script>
