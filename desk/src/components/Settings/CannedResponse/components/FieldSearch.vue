<template>
  <div class="relative">
    <ComboboxRoot class="relative" :multiple="false" v-model:open="isOpen">
      <ComboboxAnchor>
        <ComboboxTrigger>
          <Button :label="__('Field')" size="sm" icon-left="plus" />
        </ComboboxTrigger>
      </ComboboxAnchor>

      <ComboboxContent
        class="absolute z-10 mt-1 w-64 bg-white overflow-hidden rounded-lg shadow-sm border"
      >
        <div class="p-2 relative">
          <ComboboxInput
            class="text-base rounded h-7 py-1.5 pl-2 pr-2 border border-[--surface-gray-2] bg-surface-gray-2 placeholder-ink-gray-4 hover:border-outline-gray-modals hover:bg-surface-gray-3 focus:bg-surface-white focus:border-outline-gray-4 focus:shadow-sm focus:ring-0 focus-visible:ring-2 focus-visible:ring-outline-gray-3 text-ink-gray-8 transition-colors w-full dark:[color-scheme:dark]"
            :placeholder="__('Search')"
          />
        </div>
        <ComboboxViewport
          class="flex flex-col gap-0.5 max-h-60 overflow-y-auto p-2 pt-0"
        >
          <ComboboxEmpty class="text-base text-ink-gray-5 p-2 text-center">
            {{ __("No fields found") }}
          </ComboboxEmpty>
          <template v-for="field in metaFieldsList" :key="field.value">
            <ComboboxItem
              as-child
              :value="field.value"
              @select.prevent.stop="onFieldSelected(field)"
            >
              <div
                class="p-2 cursor-pointer hover:bg-gray-50 text-base flex items-center justify-between rounded"
              >
                {{ field.label }}
              </div>
            </ComboboxItem>
          </template>
        </ComboboxViewport>
      </ComboboxContent>
    </ComboboxRoot>
  </div>
</template>

<script setup lang="ts">
import { getMeta } from "@/stores/meta";
import { watchDebounced } from "@vueuse/core";
import {
  ComboboxAnchor,
  ComboboxContent,
  ComboboxEmpty,
  ComboboxInput,
  ComboboxItem,
  ComboboxRoot,
  ComboboxTrigger,
  ComboboxViewport,
} from "reka-ui";
import { computed, ref } from "vue";
import { userFields } from "../cannedResponse";

const isOpen = ref(false);
const fieldSearchQuery = ref("");
const ticketMeta = getMeta("HD Ticket");

watchDebounced(
  fieldSearchQuery,
  (newQuery) => {
    metaFieldsList.value = metaFields.value.filter((f) =>
      f.label.toLowerCase().includes(newQuery.toLowerCase())
    );
  },
  {
    debounce: 250,
  }
);

const metaFields = computed(() => {
  return ticketMeta
    .getFields()
    .filter(
      (f) =>
        f.fieldtype !== "Tab Break" &&
        f.fieldtype !== "Section Break" &&
        Boolean(f.label)
    )
    .map((f) => ({ label: f.label, value: f.fieldname }))
    .concat(userFields);
});

const metaFieldsList = ref(metaFields.value);

const emit = defineEmits(["onFieldSelected"]);

const onFieldSelected = (field) => {
  isOpen.value = false;
  emit("onFieldSelected", field);
};
</script>
