<template>
  <div class="flex-col text-base flex-1">
    <!-- Summary Block Header -->
    <div class="mb-1 ml-0.5 flex items-center justify-between">
      <!-- Activity Info -->
      <div class="text-gray-600 flex items-center gap-2">
        <Avatar
          size="md"
          :label="activity.summarizer"
          :image="getUser(activity.summarizedBy).user_image"
        />
        <p>
          <span class="font-medium text-gray-800">
            {{ activity.summarizer }}
          </span>
          <span> generated a</span>
          <span class="max-w-xs truncate font-medium text-gray-800">
            summary
          </span>
        </p>
      </div>

      <!-- Time Ago -->
      <div class="flex items-center gap-1">
        <Tooltip :text="dateFormat(activity.creation, dateTooltipFormat)">
          <span class="pl-0.5 text-sm text-gray-600">
            {{ timeAgo(activity.creation) }}
          </span>
        </Tooltip>
      </div>
    </div>

    <div class="rounded bg-gray-50 transition-colors px-4 py-3">
      <!-- Summary Snippet -->
      <div class="flex items-center justify-between">
        <p title="Summary snippet" class="text-p-sm">{{ activity.snippet }}</p>
        <Button
          variant="ghost"
          :icon="show ? 'chevron-up' : 'chevron-down'"
          @click="show = !show"
        >
        </Button>
      </div>

      <div
        v-if="show"
        class="border-0 border-t my-3 border-outline-gray-modals"
      />

      <!-- Summary Details -->
      <p v-if="show">
        <TextEditor
          ref="editorRef"
          :editor-class="[
            'prose-f shrink text-p-sm transition-all duration-300 ease-in-out block w-full content',
            getFontFamily(activity.content),
          ]"
          :content="activity.content"
          :editable="false"
          :bubble-menu="[]"
          @change="() => {}"
        >
        </TextEditor>
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useUserStore } from "@/stores/user";
import { SummaryActivity } from "@/types";
import { dateFormat, dateTooltipFormat, getFontFamily, timeAgo } from "@/utils";
import { Avatar, Button, TextEditor } from "frappe-ui";
import { PropType, ref, toRef, watch } from "vue";

const props = defineProps({
  activity: {
    type: Object as PropType<SummaryActivity>,
    required: true,
  },
  isLast: {
    type: Boolean,
    default: false,
  },
});

const show = toRef(props.isLast);
const { getUser } = useUserStore();
</script>
