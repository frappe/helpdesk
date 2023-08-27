<template>
  <Dialog
    :options="{ title: 'Canned responses', size: '4xl' }"
    @close="() => $emit('update:modelValue', false)"
  >
    <template #body-content>
      <FormControl
        v-model="search"
        type="text"
        class="mb-2 w-full"
        placeholder="Search"
      />
      <div class="grid grid-cols-3 gap-2">
        <HCard
          v-for="item in responses.data"
          :key="item.name"
          :title="item.title"
          @click="
            () => {
              $emit('select', item.message);
              $emit('update:modelValue', false);
            }
          "
        >
          <template #description>
            <!-- eslint-disable-next-line vue/no-v-html -->
            <span class="prose-f" v-html="item.message" />
          </template>
        </HCard>
      </div>
    </template>
  </Dialog>
</template>

<script setup lang="ts">
import { ref, watch } from "vue";
import { createListResource, Dialog, FormControl } from "frappe-ui";
import { HCard } from "@/components";

interface E {
  (event: "select", content: string): void;
  (event: "update:modelValue", value: boolean): void;
}

defineEmits<E>();
const search = ref("");
const responses = createListResource({
  doctype: "HD Canned Response",
  auto: true,
  debounce: 500,
  pageLength: 9,
  fields: ["name", "title", "message"],
});
watch(search, (s) => {
  responses.update({
    filters: {
      title: ["like", `%${s}%`],
    },
  });
  responses.reload();
});
</script>
