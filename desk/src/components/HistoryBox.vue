<template>
  <div class="flex-1">
    <div
      class="mt-0.5 flex justify-between text-base items-start md:items-center"
    >
      <div
        v-if="relatedActivities.length > 1"
        class="inline-flex flex-wrap gap-1.5 text-ink-gray-8 font-medium w-4/5"
      >
        <span>{{ `${show_others ? __("Hide ") : __("Show ")}` }}</span>
        <span>+{{ relatedActivities.length }} </span>
        <span>{{ __("changes from") }} </span>
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
      <div class="text-ink-gray-5 w-4/6 text-p-base" v-else>
        <span class="font-medium text-ink-gray-8">
          {{ user }}
        </span>
        <span> {{ content }}</span>
      </div>

      <div class="text-ink-gray-5 text-sm w-2/6 flex justify-end">
        <TimelineTimestamp :date="creation" />
      </div>
    </div>
    <div v-if="show_others" class="space-y-2.5 mt-3.5">
      <div
        v-for="relatedActivity in relatedActivities"
        :key="relatedActivity.creation"
        class="flex justify-between text-base"
      >
        <div class="text-ink-gray-5 w-4/6">
          <span class="font-medium text-ink-gray-8">
            {{ relatedActivity.user }}
          </span>
          <span> {{ relatedActivity.content }}</span>
        </div>
        <TimelineTimestamp :date="relatedActivity.creation" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { SelectIcon } from "@/components/icons";
import { computed, ref } from "vue";
import TimelineTimestamp from "./TimelineTimestamp.vue";
const props = defineProps({
  activity: {
    type: Object,
    required: true,
  },
});

const { user, content, creation } = props.activity;
const relatedActivities = computed(() => props.activity.relatedActivities);

let show_others = ref(false);
</script>
