<template>
  <div class="group relative w-full">
    <component
      :is="isPhone ? PhoneControl : FormControl"
      ref="control"
      :class="isPhone ? undefined : '[&_p]:text-p-xs'"
      :type="isPhone ? undefined : type"
      :placeholder="placeholder"
      v-model="model"
      @keydown.enter.prevent="blurInput"
    >
      <template #suffix>
        <div class="flex items-center gap-1">
          <Tooltip
            v-if="isPrimary"
            :text="canTogglePrimary ? __('Remove primary') : __('Primary')"
          >
            <button
              v-if="canTogglePrimary"
              type="button"
              class="flex size-5 items-center justify-center rounded text-ink-amber-2"
              :aria-label="__('Remove primary')"
              @mousedown.prevent
              @click="$emit('setPrimary')"
            >
              <LucideStar class="size-4 fill-ink-amber-2" />
            </button>
            <span
              v-else
              class="flex size-5 items-center justify-center rounded text-ink-amber-2"
              :aria-label="__('Primary')"
            >
              <LucideStar class="size-4 fill-ink-amber-2" />
            </span>
          </Tooltip>
          <Tooltip v-else :text="__('Set as primary')">
            <button
              type="button"
              class="invisible flex size-5 items-center justify-center rounded text-ink-gray-4 group-hover:visible focus-visible:visible hover:text-ink-amber-2"
              :aria-label="__('Set as primary')"
              @mousedown.prevent
              @click="$emit('setPrimary')"
            >
              <LucideStar class="size-4" />
            </button>
          </Tooltip>
          <Tooltip v-if="canRemove" :text="__('Remove')">
            <button
              type="button"
              class="flex size-5 items-center justify-center rounded text-ink-gray-4 hover:text-ink-red-3"
              :class="
                isPrimary
                  ? ''
                  : 'invisible group-hover:visible focus-visible:visible'
              "
              :aria-label="__('Remove')"
              @mousedown.prevent
              @click="$emit('remove')"
            >
              <LucideX class="size-3.5" />
            </button>
          </Tooltip>
        </div>
      </template>
    </component>
  </div>
</template>

<script setup lang="ts">
import { __ } from "@/translation";
import { FormControl, Tooltip } from "frappe-ui";
import { computed, nextTick, onMounted, ref } from "vue";
import LucideStar from "~icons/lucide/star";
import LucideX from "~icons/lucide/x";
import PhoneControl from "../frappe-ui/PhoneControl.vue";

const props = withDefaults(
  defineProps<{
    isPrimary: boolean;
    canRemove: boolean;
    canTogglePrimary?: boolean;
    type?: "email" | "tel" | "text";
    placeholder?: string;
    autofocus?: boolean;
  }>(),
  {
    canTogglePrimary: false,
    type: "text",
    placeholder: "",
    autofocus: false,
  }
);

const model = defineModel<string>({ required: true });

defineEmits<{
  setPrimary: [];
  remove: [];
}>();

const control = ref<any>(null);
const isPhone = computed(() => props.type === "tel");

function getInputEl(): HTMLInputElement | null {
  return control.value?.$el?.querySelector?.("input") ?? null;
}

function blurInput() {
  getInputEl()?.blur();
}

onMounted(() => {
  if (props.autofocus) {
    nextTick(() => getInputEl()?.focus());
  }
});
</script>
