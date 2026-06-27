<template>
  <div class="relative gap-2 flex items-center w-full">
    <component
      :is="isPhone ? PhoneControl : FormControl"
      ref="control"
      class="flex-1"
      :class="isPhone ? undefined : '[&_p]:text-p-xs'"
      :type="isPhone ? undefined : type"
      :placeholder="placeholder"
      v-model="model"
      @keydown.enter.prevent="blurInput"
    >
      <!-- <template #suffix>
        
      </template> -->
    </component>
    <div class="flex items-center gap-0">
      <Tooltip
        v-if="isPrimary"
        :text="canTogglePrimary ? __('Remove primary') : __('Primary')"
      >
        <Button
          variant="ghost"
          :aria-label="__('Remove primary')"
          @click="$emit('setPrimary')"
        >
          <template #icon>
            <LucideStar class="size-4 fill-ink-amber-6 stroke-ink-amber-6" />
          </template>
        </Button>
      </Tooltip>
      <Tooltip v-else :text="__('Set as primary')">
        <Button
          variant="ghost"
          type="button"
          :aria-label="__('Set as primary')"
          @mousedown.prevent
          @click="$emit('setPrimary')"
        >
          <template #icon>
            <LucideStar class="size-4" />
          </template>
        </Button>
      </Tooltip>
      <Tooltip :text="__('Remove')">
        <Button
          :disabled="!canRemove"
          variant="ghost"
          type="button"
          :aria-label="__('Remove')"
          @mousedown.prevent
          @click="$emit('remove')"
        >
          <template #icon>
            <LucideX class="size-3.5" />
          </template>
        </Button>
      </Tooltip>
    </div>
  </div>
</template>

<script setup lang="ts">
import { __ } from "@/translation";
import { Button, FormControl, Tooltip } from "frappe-ui";
import { computed, nextTick, onMounted, ref } from "vue";
import LucideStar from "~icons/lucide/star";
import LucideX from "~icons/lucide/x";
import PhoneControl from "../frappe-ui/PhoneControl/PhoneControl.vue";

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
