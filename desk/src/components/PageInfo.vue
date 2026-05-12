<template>
  <div class="flex items-center justify-between p-5 pb-0">
    <div class="gap-x-3 flex h-full">
      <Avatar
        :size="avatar.size ?? '3xl'"
        :shape="avatar.shape ?? 'square'"
        :label="avatar.label"
        :image="avatar.image"
        class="h-[52px] w-[52px]"
      />
      <div
        class="flex flex-col h-full gap-1.5"
        :class="[
          (isMobileView || !docInfo?.length) &&
            'flex-1 items-center justify-center',
        ]"
      >
        <div class="flex gap-2 items-center">
          <p class="font-medium text-ink-gray-8 text-xl">
            {{ avatar.label }}
          </p>
          <Tooltip text="Invite sent. Waiting for the user to accept.">
            <Badge
              v-if="props.badge"
              :label="props.badge"
              :theme="'orange'"
              class="mt-[1px]"
            />
          </Tooltip>
        </div>
        <div
          v-if="!isMobileView && docInfo && docInfo.length"
          class="flex items-center gap-x-1.5"
        >
          <template v-for="(item, index) in docInfo" :key="index">
            <template v-if="item.condition !== false">
              <span
                v-if="
                  docInfo.slice(0, index).some((i) => i.condition !== false)
                "
                class="text-ink-gray-4"
                >•</span
              >
              <div class="flex items-center gap-x-1">
                <component
                  v-if="item.icon"
                  :is="item.icon"
                  class="h-4 w-4 text-ink-gray-6"
                />
                <span v-if="item.value" class="text-sm text-ink-gray-8">{{
                  item.value
                }}</span>
                <template v-else-if="item.component">
                  <component :is="item.component" />
                </template>
              </div>
            </template>
          </template>
        </div>
      </div>
    </div>
    <slot name="actions" />
  </div>
</template>

<script setup lang="ts">
import { useScreenSize } from "@/composables/screen";
import { Avatar, Badge, Tooltip, type AvatarProps } from "frappe-ui";

interface DocInfoItem {
  icon?: any;
  value?: string;
  component?: any;
  condition?: boolean;
}

const props = withDefaults(
  defineProps<{
    avatar: AvatarProps;
    docInfo?: DocInfoItem[];
    badge?: string;
  }>(),
  {
    docInfo: () => [],
    badge: () => "",
  }
);

const { isMobileView } = useScreenSize();
</script>
