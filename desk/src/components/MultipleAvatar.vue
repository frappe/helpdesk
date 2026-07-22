<template>
  <div v-if="_avatars?.length" class="me-1.5 flex cursor-pointer items-center">
    <div
      v-if="_avatars?.length == 1"
      class="flex items-center gap-2 text-base line-clamp-1"
    >
      <Tooltip :text="_avatars[0].name">
        <Avatar
          shape="circle"
          :image="_avatars[0].image"
          :label="_avatars[0].label"
          size="sm"
        />
        <div class="truncate" v-if="!hideName">{{ _avatars[0].label }}</div>
      </Tooltip>
    </div>
    <template v-else>
      <Tooltip
        v-for="avatar in visibleAvatars"
        :key="avatar.name"
        :text="avatar.name"
      >
        <Avatar
          class="user-avatar -mr-1.5 ring-2 ring-[var(--surface-base)] transition hover:z-20 hover:scale-110"
          shape="circle"
          :image="avatar.image"
          :label="avatar.label"
          :size="size"
          :data-name="avatar.name"
        />
      </Tooltip>
      <Tooltip v-if="overflowCount" :text="overflowNames">
        <div
          class="user-avatar relative z-10 -mr-1.5 flex size-5 shrink-0 items-center justify-center rounded-full bg-surface-gray-3 text-xs text-ink-gray-7 ring-2 ring-[var(--surface-base)]"
        >
          +{{ overflowCount }}
        </div>
      </Tooltip>
    </template>
  </div>
</template>
<script setup lang="ts">
import { useUserStore } from "@/stores/user";
import { Avatar, Tooltip } from "frappe-ui";
import { computed } from "vue";

const props = defineProps({
  avatars: {
    type: String,
  },
  size: {
    type: String,
    default: "sm",
  },
  hideName: {
    type: Boolean,
    default: false,
  },
  // Cap the number of avatars shown; the rest collapse into a "+n" chip.
  // 0 (default) shows all, so existing callers are unaffected.
  max: {
    type: Number,
    default: 0,
  },
});
const { getUser } = useUserStore();
const _avatars = computed(() => {
  let result: any;
  try {
    result = JSON.parse(props.avatars);
  } catch (error) {
    result = props.avatars;
  }
  if (!result) return;
  if (result[0]?.hasOwnProperty("name")) {
    return result;
  }
  result = result.map((a: string) => {
    let _user = getUser(a);
    return {
      name: _user.name,
      label: _user.full_name,
      image: _user.user_image,
    };
  });
  return result;
});

const capped = computed(
  () => props.max > 0 && (_avatars.value?.length || 0) > props.max
);

const visibleAvatars = computed(() =>
  capped.value ? _avatars.value.slice(0, props.max) : _avatars.value
);

const overflowCount = computed(() =>
  capped.value ? _avatars.value.length - props.max : 0
);

const overflowNames = computed(() =>
  capped.value
    ? _avatars.value
        .slice(props.max)
        .map((a: { name: string }) => a.name)
        .join(", ")
    : ""
);
</script>
