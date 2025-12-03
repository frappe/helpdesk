<template>
  <Popover :placement="props.placement">
    <template #target="{ togglePopover }">
      <Button
        class="flex items-center justify-between min-w-36"
        @click="togglePopover()"
        :class="targetClass"
        icon-right="chevron-down"
      >
        <div class="w-full truncate">
          {{
            options?.find((option) => option.value == model)?.label || "Select"
          }}
        </div>
      </Button>
    </template>
    <template #body="{ togglePopover }">
      <div
        class="p-1 text-ink-gray-6 top-1 absolute w-44 bg-white shadow-2xl rounded"
        :class="bodyClass"
      >
        <div class="max-h-52 overflow-y-auto">
          <div
            v-for="option in options"
            :key="option.value"
            class="p-2 cursor-pointer hover:bg-surface-gray-3 text-base flex items-center justify-between rounded"
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
          @click="onReset(togglePopover)"
        />
      </div>
    </template>
  </Popover>
</template>

<script setup lang="ts">
import { Button, FeatherIcon, Popover } from "frappe-ui";

const model = defineModel();

interface Props {
  options: Array<{ value: string; label: string }>;
  targetClass?: string;
  bodyClass?: string;
  placement?: string;
}

const props = withDefaults(defineProps<Props>(), {
  placement: "bottom-start",
});

const onReset = (togglePopover: () => void) => {
  model.value = null;
  togglePopover();
};

const onChange = (value: string) => {
  model.value = value;
};
</script>
