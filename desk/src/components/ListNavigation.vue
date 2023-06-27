<template>
  <div v-if="totalCount" class="border-t text-base">
    <div class="flex items-center justify-end gap-2 text-gray-600">
      <div class="text-gray-600">
        {{ startFrom }}
        -
        {{ endAt }}
        of
        {{ totalCount }}
      </div>
      <Button
        icon="chevron-left"
        :disabled="loading || !hasPreviousPage"
        class="rounded-full"
        variant="outline"
        @click="previous"
      />
      <Button
        icon="chevron-right"
        :disabled="loading || !hasNextPage"
        class="rounded-full"
        variant="outline"
        @click="next"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, toRefs } from "vue";

const props = defineProps({
  startFrom: {
    type: Number,
    required: true,
  },
  limit: {
    type: Number,
    required: true,
  },
  totalCount: {
    type: Number,
    required: false,
    default: 0,
  },
  next: {
    type: Function,
    required: false,
    default: () => true,
  },
  previous: {
    type: Function,
    required: false,
    default: () => true,
  },
  loading: {
    type: Boolean,
    required: false,
    default: false,
  },
});

const { startFrom, limit, totalCount } = toRefs(props);
const endAt = computed(() => {
  const byLimit = startFrom.value + limit.value;
  return byLimit < totalCount.value ? byLimit : totalCount.value;
});
const hasPreviousPage = computed(() => startFrom.value > 1);
const hasNextPage = computed(() => endAt.value < totalCount.value);
</script>
