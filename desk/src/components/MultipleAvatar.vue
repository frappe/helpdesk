<template>
  <div
    v-if="avatars?.length"
    class="mr-1.5 flex cursor-pointer items-center"
    :class="[
      avatars?.length > 1 ? 'flex-row-reverse' : 'truncate [&>div]:truncate',
    ]"
  >
    <div v-if="avatars?.length == 1" class="flex items-center gap-2 text-base">
      <Tooltip :text="avatars[0].name">
        <Avatar
          shape="circle"
          :image="avatars[0].image"
          :label="avatars[0].label"
          size="sm"
        />
        <div class="truncate">{{ avatars[0].label }}</div>
      </Tooltip>
    </div>
    <Tooltip
      v-for="avatar in props.avatars"
      v-else
      :key="avatar.name"
      :text="avatar.name"
    >
      <Avatar
        class="user-avatar -mr-1.5 ring-2 ring-white transition hover:z-10 hover:scale-110"
        shape="circle"
        :image="avatar.image"
        :label="avatar.label"
        :size="size"
        :data-name="avatar.name"
      />
    </Tooltip>
  </div>
</template>
<script setup lang="ts">
import { Avatar, Tooltip } from "frappe-ui";

const props = defineProps({
  avatars: {
    type: Array,
    default: () => [],
  },
  size: {
    type: String,
    default: "md",
  },
});
</script>
