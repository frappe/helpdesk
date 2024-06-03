<template>
  <div class="flex items-center gap-2">
    <Avatar :label="user.name" :image="user.user_image" v-bind="$attrs" />
    <span
      v-if="expand"
      class="truncate"
      :class="{
        'text-gray-900': strong,
        'font-medium': strong,
      }"
    >
      {{ name }}
    </span>
  </div>
</template>
<script setup lang="ts">
import { Avatar } from "frappe-ui";
import { useUserStore } from "@/stores/user";
const userStore = useUserStore();

const props = defineProps({
  name: {
    type: String,
    required: true,
  },
  expand: {
    type: Boolean,
    default: false,
  },
  strong: {
    type: Boolean,
    default: false,
  },
});
const user = userStore.getUser(props.name);
</script>
