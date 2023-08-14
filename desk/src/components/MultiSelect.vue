<template>
  <div class="flex flex-wrap gap-2 rounded-lg bg-gray-100 p-2">
    <Button
      v-for="item in items"
      :key="item.value"
      :label="item.label"
      icon-right="x"
      class="h-max w-max select-none rounded bg-white p-1 shadow"
      @click="remove(item)"
    />
    <Input
      v-model="input"
      class="w-full"
      :placeholder="placeholder"
      @keyup.enter="add({ label: input, value: input })"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, toRefs } from "vue";
import { Button, Input } from "frappe-ui";
import { createToast } from "@/utils";

type Item = {
  label: string;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  value: any;
};

const props = defineProps({
  items: {
    type: Array<Item>,
    required: true,
  },
  placeholder: {
    type: String,
    required: false,
    default: "Type...",
  },
  validate: {
    type: Function,
    required: false,
    default: () => false,
  },
});

const emit = defineEmits<{
  (event: "update:items", items: Array<Item>): void;
}>();

const { items } = toRefs(props);
const input = ref("");

function add(item: Item) {
  const err = props.validate(item);

  if (err) {
    createToast({
      title: err,
      icon: "x",
      iconClasses: "text-red-500",
    });

    return;
  }

  const res = [...items.value, item];
  emit("update:items", res);
  input.value = "";
}

function remove(item: Item) {
  const res = new Set(items.value);
  res.delete(item);
  emit("update:items", Array.from(res));
}
</script>
