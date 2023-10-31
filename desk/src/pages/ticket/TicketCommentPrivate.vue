<template>
  <div class="my-4 rounded border bg-cyan-50 p-4">
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
      <div class="flex items-center gap-1">
        <Button
          variant="outline"
          :label="isPinned ? 'Unpin' : 'Pin'"
          @click="
            () => {
              comments.setValue.submit({
                name,
                is_pinned: !isPinned,
              });
            }
          "
        />
        <Button
          v-if="user.email === authStore.userId"
          label="Delete"
          theme="red"
          variant="outline"
          @click="() => comments.delete.submit(props.name)"
        />
      </div>
    </div>
    <!-- eslint-disable-next-line vue/no-v-html -->
    <span class="prose-f" v-html="content"></span>
  </div>
</template>

<script setup lang="ts">
import { inject } from "vue";
import { dayjs } from "@/dayjs";
import { useAuthStore } from "@/stores/auth";
import { UserInfo } from "@/types";
import { UserAvatar } from "@/components";
import { Comments } from "./symbols";

const props = defineProps<{
  content: string;
  date: string;
  isPinned: number;
  name: string;
  user: UserInfo;
}>();
const authStore = useAuthStore();
const comments = inject(Comments);
</script>
