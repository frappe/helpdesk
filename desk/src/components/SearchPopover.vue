<template>
  <Popover
    :popover-class="popoverClass.length > 0 ? popoverClass : ''"
    class="flex w-full"
  >
    <template #target="{ open, close }">
      <div class="flex flex-col gap-1 w-full">
        <slot name="label"></slot>
        <FormControl
          type="text"
          class="w-full focus:outline-none outline-none border-inherit shadow-none"
          v-bind="$attrs"
          v-model="query"
          @update:model-value="(e:string)=>{
            if (e.length >= 3) {
              open();
            } else {
            close();
            }
          }"
        >
          <template #prefix>
            <Icon icon="lucide:search" class="h-4 w-4 text-gray-500" />
          </template>
        </FormControl>
      </div>
    </template>
    <template #body-main>
      <!-- Searched Articles -->
      <div class="max-h-[320px] md:max-h-[420px] overflow-scroll flex flex-col">
        <SearchArticles
          :query="query"
          :hideViewAll="true"
          class="p-3 py-2 border-0 pt-2"
        />
      </div>
    </template>
  </Popover>
</template>

<script setup lang="ts">
import { FormControl, Popover } from "frappe-ui";
import SearchArticles from "./SearchArticles.vue";
import { ModelRef } from "vue";
import { Icon } from "@iconify/vue";

interface P {
  popoverClass: Array<string>;
  inputOptions?: Record<string, unknown>;
}

//   with defaults defineProps []
const props = withDefaults(defineProps<P>(), {
  popoverClass: () => [],
  inputOptions: () => ({}),
});

const query: ModelRef<string> = defineModel();
</script>

<style scoped></style>
