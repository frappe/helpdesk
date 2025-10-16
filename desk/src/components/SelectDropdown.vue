<template>
  <Popover :placement="'bottom-start'">
    <template #target="{ togglePopover }">
      <div
        class="flex items-center justify-between text-base rounded h-7 py-1.5 pl-2 pr-2 border border-[--surface-gray-2] bg-surface-gray-2 placeholder-ink-gray-4 hover:border-outline-gray-modals hover:bg-surface-gray-3 focus:bg-surface-white focus:border-outline-gray-4 focus:shadow-sm focus:ring-0 focus-visible:ring-2 focus-visible:ring-outline-gray-3 text-ink-gray-8 transition-colors w-full dark:[color-scheme:dark] cursor-default gap-2 min-w-36"
        @click="togglePopover()"
        :class="targetClass"
      >
        <div class="w-full truncate">
          {{
            options?.find((option) => option.value == model)?.label || "Select"
          }}
        </div>
        <FeatherIcon name="chevron-down" class="size-4" />
      </div>
    </template>
    <template #body="{ togglePopover }">
      <div
        class="p-1 text-ink-gray-6 top-1 absolute w-full bg-white shadow-2xl rounded"
        :class="bodyClass"
      >
        <div class="max-h-52 overflow-y-auto">
          <div
            v-for="option in options"
            :key="option.value"
            class="p-2 cursor-pointer hover:bg-gray-50 text-base flex items-center justify-between rounded"
            @click="
              () => {
                onChange(option.value);
                togglePopover();
              }
            "
          >
            <div class="w-full truncate">
              {{ option.label }}
            </div>
            <FeatherIcon
              v-if="model == option.value"
              name="check"
              class="size-4 ml-2"
            />
          </div>
        </div>
        <hr class="my-1" />
        <Button
          variant="ghost"
          :label="__('Reset')"
          icon-left="refresh-ccw"
          class="w-full focus-visible:ring-0"
          @click="onReset"
        />
      </div>
    </template>
  </Popover>
</template>

<script setup lang="ts">
import { Popover } from "frappe-ui";
import { PopoverProps } from "frappe-ui/src/components/Popover/types";

const model = defineModel();

const emit = defineEmits(["update:modelValue", "onReset", "onChange"]);

interface Props {
  options: Array<{ value: string; label: string }>;
  targetClass?: string;
  bodyClass?: string;
  placement?: PopoverProps["placement"];
}

const props = withDefaults(defineProps<Props>(), {
  placement: "bottom-start",
});

const onReset = () => {
  emit("onReset");
  emit("update:modelValue", null);
  model.value = null;
};

const onChange = (value: string) => {
  emit("onChange", value);
  emit("update:modelValue", value);
  model.value = value;
};
</script>
