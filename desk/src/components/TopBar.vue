<template>
  <div class="flex items-center justify-between gap-2 border-b px-6 py-3">
    <div class="space-y-2">
      <div class="flex items-center gap-3">
        <IconChevronLeft
          v-if="!isEmpty(backTo)"
          class="h-4 w-4 cursor-pointer text-gray-700"
          @click="goBack"
        />
        <div class="text-xl font-medium text-gray-900">
          <div class="line-clamp-1">
            {{ title }}
          </div>
        </div>
      </div>
      <div
        v-if="slots.bottom"
        :class="{
          'ml-7': !isEmpty(backTo),
        }"
      >
        <slot name="bottom" />
      </div>
    </div>
    <slot name="right" />
  </div>
</template>

<script setup lang="ts">
import { PropType, useSlots } from "vue";
import { useRouter, RouteLocationOptions } from "vue-router";
import { isEmpty } from "lodash";
import IconChevronLeft from "~icons/lucide/chevron-left";

const props = defineProps({
  title: {
    type: String,
    required: true,
  },
  backTo: {
    type: Object as PropType<RouteLocationOptions>,
    required: false,
    default: () => ({}),
  },
});
const router = useRouter();
const slots = useSlots();

function goBack() {
  function fallback() {
    router.push(props.backTo);
  }

  const previousPage = window.history.state.back;
  if (!previousPage) fallback();
  const route = router.resolve({ path: window.history.state.back });
  if (route.name === props.backTo) router.back();
  else fallback();
}
</script>
