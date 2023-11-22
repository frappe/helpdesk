<template>
  <div class="bg-cyan-50 px-5 py-3">
    <div class="mb-4 flex items-center justify-between">
      <div class="flex items-center gap-0.5 text-base">
        <UserAvatar v-bind="user" size="lg" expand strong />
        <LucideDot class="h-4 w-4 text-gray-500" />
        <Tooltip :text="dayjs(date).long()">
          <div class="text-gray-600">
            {{ dayjs(date).fromNow() }}
          </div>
        </Tooltip>
      </div>
      <div class="flex items-center">
        <Button
          v-if="user.email === authStore.userId"
          label="Delete"
          theme="red"
          variant="ghost"
          @click="() => comments.delete.submit(props.name)"
        >
          <template #icon>
            <LucideTrash2 class="h-4 w-4" />
          </template>
        </Button>
        <Button
          variant="ghost"
          @click="
            () => {
              comments.setValue.submit({
                name,
                is_pinned: !isPinned,
              });
            }
          "
        >
          <template #icon>
            <LucidePinOff v-if="isPinned" class="h-4 w-4 rotate-45" />
            <LucidePin v-else class="h-4 w-4 rotate-45" />
          </template>
        </Button>
      </div>
    </div>
    <!-- eslint-disable-next-line vue/no-v-html -->
    <span class="prose-f" v-html="content"></span>
    <div v-if="attachments.length" class="flex flex-wrap gap-2">
      <AttachmentItem
        v-for="a in attachments"
        :key="a.file_url"
        :label="a.file_name"
        :url="a.file_url"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { inject } from 'vue';
import { dayjs } from '@/dayjs';
import { useAuthStore } from '@/stores/auth';
import { UserInfo } from '@/types';
import { UserAvatar } from '@/components';
import { Comments } from './symbols';

const props = withDefaults(
  defineProps<{
    content: string;
    date: string;
    isPinned: number;
    name: string;
    user: UserInfo;
    attachments?: any[];
  }>(),
  {
    attachments: () => [],
  }
);
const authStore = useAuthStore();
const comments = inject(Comments);
</script>
