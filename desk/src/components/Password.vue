<template>
  <FormControl
    :type="show ? 'text' : 'password'"
    :value="modelValue || value"
    v-bind="$attrs"
    @keydown.meta.i.prevent="show = !show"
    @keydown.ctrl.i.prevent="show = !show"
  >
    <template #prefix v-if="$slots.prefix">
      <slot name="prefix" />
    </template>
    <template #suffix>
      <Tooltip>
        <template #body>
          <div
            class="rounded bg-surface-gray-7 py-1.5 px-2 text-xs text-ink-white shadow-xl"
          >
            <span class="flex items-center gap-1">
              {{ show ? "Hide Password" : "Show Password" }}
            </span>
          </div>
        </template>
        <div>
          <component
            v-show="showEye"
            :is="show ? LucideEyeOff : LucideEye"
            class="h-3 cursor-pointer mr-1"
            @click="show = !show"
          />
        </div>
      </Tooltip>
    </template>
  </FormControl>
</template>
<script setup lang="ts">
import LucideEye from "~icons/lucide/eye";
import LucideEyeOff from "~icons/lucide/eye-off";
import { ref, computed } from "vue";
import { FormControl, Tooltip } from "frappe-ui";

const props = defineProps({
  value: {
    type: String,
    default: "",
  },
  modelValue: {
    type: String,
    default: "",
  },
});

const show = ref(false);
const showEye = computed(() => {
  let v = props.modelValue || props.value;
  return !v?.includes("*");
});
</script>
