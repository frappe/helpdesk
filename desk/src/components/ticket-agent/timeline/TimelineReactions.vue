<template>
  <div class="flex flex-wrap items-center gap-1.5 pt-1.5">
    <Popover side="top" align="start">
      <template #trigger>
        <Button variant="ghost" class="text-ink-gray-5 -ml-1.5">
          <template #icon>
            <ReactionIcon class="size-4" />
          </template>
        </Button>
      </template>
      <template #default="{ close }">
        <div class="p-2">
          <div class="grid grid-cols-6 gap-2">
            <button
              v-for="emoji in PRESET_EMOJIS"
              :key="emoji"
              class="size-6 flex items-center justify-center rounded-4 hover:bg-surface-gray-2 text-md transition-colors"
              @click="
                emit('toggle', emoji);
                close();
              "
            >
              {{ emoji }}
            </button>
          </div>
        </div>
      </template>
    </Popover>

    <Tooltip bare v-for="reaction in reactions" :key="reaction.emoji">
      <template #content>
        <div
          class="bg-surface-gray-10 px-2 py-1 text-center text-p-xs text-ink-base shadow-xl rounded-4"
        >
          {{ reaction.users.map((u) => u.full_name).join(", ") }}
        </div>
      </template>
      <button
        class="flex items-center gap-1 px-2 py-1 rounded-full text-sm transition-colors"
        :class="
          reaction.current_user_reacted
            ? 'bg-surface-blue-2 text-ink-blue-6 hover:bg-surface-blue-3'
            : 'bg-surface-gray-3 text-ink-gray-6 hover:bg-surface-gray-4'
        "
        @click="emit('toggle', reaction.emoji)"
      >
        <span>{{ reaction.emoji }}</span>
        <span class="font-medium">{{ reaction.count }}</span>
      </button>
    </Tooltip>
  </div>
</template>

<script setup lang="ts">
import ReactionIcon from "@/components/icons/ReactionIcon.vue";
import { Button, Popover, Tooltip } from "frappe-ui";

export interface CommentReaction {
  emoji: string;
  count: number;
  users: Array<{ user: string; full_name: string }>;
  current_user_reacted: boolean;
}

const PRESET_EMOJIS = ["👍", "👎", "❤️", "🎉", "👀", "✅"];

defineProps<{ reactions: CommentReaction[] }>();
const emit = defineEmits<{ toggle: [emoji: string] }>();
</script>
