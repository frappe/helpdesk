<template>
  <div
    class="flex items-center gap-1 rounded-md bg-gray-100 px-2 py-1 text-sm text-gray-800"
  >
    <Avatar :image="image" :label="name" size="sm" />
    {{ name }}
  </div>
</template>

<script setup lang="ts">
import { toRefs } from "vue";
import { Avatar } from "frappe-ui";

const props = defineProps({
  name: {
    type: String,
    required: true,
  },
  image: {
    type: String,
    required: false,
    default: null,
  },
});

const { name, image } = toRefs(props);
</script>
