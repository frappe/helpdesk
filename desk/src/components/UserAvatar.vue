<template>
  <div class="flex items-center gap-2">
    <Avatar
      :label="user.name"
      :image="user.user_image"
      v-bind="$attrs"
      v-if="!hideAvatar"
    />
    <span
      v-if="expand"
      class="truncate capitalize text-base text-ink-gray-9 font-medium"
      :class="{
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
  hideAvatar: {
    type: Boolean,
    default: false,
  },
});
const user = userStore.getUser(props.name);
</script>
