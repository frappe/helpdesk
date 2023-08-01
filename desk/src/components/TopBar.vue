<template>
  <div class="flex items-center justify-between gap-2 border-b px-6 py-3">
    <div class="space-y-2">
      <div class="flex items-center gap-3">
        <Icon
          v-if="!isEmpty(backTo)"
          icon="lucide:chevron-left"
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
import { useSlots } from "vue";
import { useRouter, RouteLocationNamedRaw } from "vue-router";
import { isEmpty } from "lodash";
import { Icon } from "@iconify/vue";

interface P {
  title: string;
  backTo?: RouteLocationNamedRaw;
}

const props = withDefaults(defineProps<P>(), {
  backTo: () => ({}),
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
  if (route.name === props.backTo.name) router.back();
  else fallback();
}
</script>
