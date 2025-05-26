<template>
  <div class="flex-1">
    <div
      class="mt-1.5 flex justify-between text-base items-start md:items-center"
    >
      <div
        v-if="relatedActivities.length > 1"
        class="inline-flex flex-wrap gap-1.5 text-ink-gray-8 font-medium w-4/5"
      >
        <span>{{ `${show_others ? "Hide " : "Show "}` }}</span>
        <span>+{{ relatedActivities.length }} </span>
        <span>changes from </span>
        <span>{{ user }}</span>

        <Button
          class="!size-4"
          variant="ghost"
          @click="show_others = !show_others"
        >
          <template #icon>
            <SelectIcon />
          </template>
        </Button>
      </div>
      <div class="text-gray-600 w-4/6" v-else>
        <span class="font-medium text-gray-800">
          {{ user }}
        </span>
        <span> {{ content }}</span>
      </div>

      <Tooltip :text="dateFormat(creation, dateTooltipFormat)">
        <div class="text-gray-600 text-sm w-2/6 flex justify-end">
          {{ timeAgo(creation) }}
        </div>
      </Tooltip>
    </div>
    <div v-if="show_others">
      <div
        v-for="relatedActivity in relatedActivities"
        :key="relatedActivity.creation"
        class="mt-2 flex justify-between text-base"
      >
        <div class="text-gray-600 w-4/6">
          <span class="font-medium text-gray-800">
            {{ relatedActivity.user }}
          </span>
          <span> {{ relatedActivity.content }}</span>
        </div>
        <Tooltip
          :text="dateFormat(relatedActivity.creation, dateTooltipFormat)"
        >
          <div class="text-gray-600 text-sm w-2/6 flex justify-end">
            {{ timeAgo(relatedActivity.creation) }}
          </div>
        </Tooltip>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { SelectIcon } from "@/components/icons";
import { dateFormat, dateTooltipFormat, timeAgo } from "@/utils";
import { ref } from "vue";
const props = defineProps({
  activity: {
    type: Object,
    required: true,
  },
});

const { user, content, creation, relatedActivities } = props.activity;

let show_others = ref(false);
</script>
