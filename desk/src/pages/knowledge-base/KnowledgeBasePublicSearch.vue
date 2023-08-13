<template>
  <Dialog
    :options="{ size: 'xl', position: 'top' }"
    :model-value="modelValue"
    @update:model-value="emit('update:modelValue', !modelValue)"
    @after-leave="articles.data = null"
  >
    <template #body>
      <div>
        <Combobox nullable @update:model-value="onSelection">
          <div class="relative">
            <div class="pl-4.5 absolute inset-y-0 left-0 flex items-center">
              <Icon icon="lucide:search" class="h-4 w-4" />
            </div>
            <ComboboxInput
              placeholder="Search"
              class="pl-11.5 pr-4.5 w-full border-none bg-transparent py-3 text-base text-gray-800 placeholder:text-gray-500 focus:ring-0"
              autocomplete="off"
              @input="onInput"
            />
          </div>
          <ComboboxOptions
            class="max-h-96 overflow-auto border-t border-gray-100 text-base"
            :class="{
              'py-2.5': !!articles.data,
            }"
            static
            hold
          >
            <ComboboxOption
              v-for="article in articles.data"
              :key="article.name"
              v-slot="{ active }"
              :value="article"
              class="px-2.5"
            >
              <div
                class="flex w-full min-w-0 items-center gap-1 rounded p-2 text-base font-medium text-gray-800"
                :class="{ 'bg-gray-200': active }"
              >
                <span
                  class="overflow-hidden text-ellipsis whitespace-nowrap text-gray-700"
                >
                  {{ article.category_name }}
                </span>
                <span class="text-gray-700"> / </span>
                <span class="overflow-hidden text-ellipsis whitespace-nowrap">
                  {{ article.title }}
                </span>
              </div>
            </ComboboxOption>
          </ComboboxOptions>
        </Combobox>
      </div>
    </template>
  </Dialog>
</template>

<script setup lang="ts">
import { toRef } from "vue";
import { createListResource, Dialog } from "frappe-ui";
import {
  Combobox,
  ComboboxInput,
  ComboboxOptions,
  ComboboxOption,
} from "@headlessui/vue";
import { Icon } from "@iconify/vue";
import { useRouter } from "vue-router";
import { KB_PUBLIC_ARTICLE } from "@/router";

interface P {
  modelValue: boolean;
}

interface E {
  (event: "update:modelValue", value: boolean): void;
}

const props = defineProps<P>();
const emit = defineEmits<E>();
const router = useRouter();
const modelValue = toRef(props, "modelValue");
const articles = createListResource({
  doctype: "HD Article",
  fields: ["name", "title", "category.category_name"],
  filters: {
    status: "Published",
  },
  orderBy: "views desc",
  pageLength: 99999,
  debounce: 500,
  auto: false,
  transform: (data) => {
    for (const d of data) {
      d.route = {
        name: KB_PUBLIC_ARTICLE,
        params: {
          articleId: d.name,
        },
      };
    }
    return data;
  },
});

function onInput(e) {
  articles.update({
    filters: {
      title: ["like", `%${e.target.value}%`],
    },
  });
  articles.reload();
}

function onSelection(val) {
  if (val) {
    emit("update:modelValue", !modelValue.value);
    router.push(val.route);
  }
}
</script>
