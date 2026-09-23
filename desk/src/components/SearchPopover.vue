<template>
  <Popover>
    <template #trigger="{ close, toggle }">
      <!--
        Typing opens this, not clicking. reka turns the trigger's root into the
        toggle, so the field stops its own click before it reaches that root.
      -->
      <div>
        <div class="flex flex-col gap-1 w-full" @click.stop>
          <slot name="label"></slot>
          <FormControl
            type="text"
            class="w-full focus:outline-none outline-none border-inherit shadow-none"
            v-bind="$attrs"
            v-model="query"
            @update:model-value="
              (e: string) => {
                if (e.length >= 3) {
                  toggle(true);
                } else {
                  close();
                }
              }
            "
          >
            <template #prefix>
              <LucideSearch class="size-4 text-ink-gray-4" />
            </template>
          </FormControl>
        </div>
      </div>
    </template>
    <template #default>
      <!-- Searched Articles -->
      <div
        class="max-h-[320px] md:max-h-[420px] overflow-scroll flex flex-col"
        :class="popoverClass"
      >
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
import { ModelRef } from "vue";
import SearchArticles from "./SearchArticles.vue";

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
