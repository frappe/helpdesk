<template>
  <div class="my-4 rounded border bg-gray-50 p-4">
    <div class="mb-4 flex items-center justify-between">
      <div class="flex items-center gap-0.5 text-base">
        <UserAvatar v-bind="user" size="lg" expand strong />
        <Icon icon="lucide:dot" class="text-gray-500" />
        <Tooltip :text="dayjs(date).long()">
          <div class="text-gray-600">
            {{ dayjs(creation).format("MMMM D, YYYY") }}
          </div>
        </Tooltip>
        <Icon icon="lucide:dot" class="text-gray-500" />
        <div class="text-gray-600">Duration: {{ duration }} minutes</div>
      </div>
      <div class="flex items-center gap-1.5 px-2">
        <div style="min-width: max-content">
          <Badge label="Time Entry" theme="blue" variant="outline" />
        </div>
        <component :is="LucideTimer" class="h-4 w-4" />
      </div>
    </div>
    <!-- eslint-disable-next-line vue/no-v-html -->
    <span class="prose-f" v-html="content"></span>
  </div>
</template>

<script setup lang="ts">
import { toRefs } from "vue";
import { Badge, Tooltip } from "frappe-ui";
import { Icon } from "@iconify/vue";
import { dayjs } from "@/dayjs";
import { UserInfo } from "@/types";
import { UserAvatar } from "@/components";
import LucideTimer from "~icons/lucide/timer";

interface P {
  content: string;
  creation: string;
  duration: string;
  user: UserInfo;
}

const props = defineProps<P>();
const { content, creation, duration, user } = toRefs(props);
</script>
