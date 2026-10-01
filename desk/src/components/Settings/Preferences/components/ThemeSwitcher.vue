<template>
  <div class="flex flex-col gap-4 mt-6">
    <div class="flex flex-col gap-1">
      <slot name="title">
        <span class="text-base-medium text-ink-gray-8">{{ __("Theme") }}</span>
      </slot>
      <slot name="description">
        <span class="text-p-sm text-ink-gray-6">
          {{ __("Switch between light, dark, or system theme") }}</span
        >
      </slot>
    </div>
    <div>
      <slot name="content">
        <div class="flex items-center gap-3" role="radiogroup">
          <div
            v-for="option in themeOptions"
            :key="option.value"
            class="flex-1 rounded-lg border cursor-pointer min-h-[42px]"
            :class="
              theme === option.value
                ? 'border-outline-gray-7'
                : 'border-outline-elevation-2'
            "
            @click="theme = option.value"
          >
            <div :class="{ flex: option.panes.length > 1 }">
              <div
                v-for="(pane, index) in option.panes"
                :key="index"
                :class="pane.containerClass"
              >
                <div :class="pane.screenClass">
                  <div
                    class="flex gap-[3px] py-[3px] px-1 border-b"
                    :class="
                      pane.tone === 'light'
                        ? 'border-gray-100'
                        : 'border-gray-800'
                    "
                  >
                    <div class="size-1.5 bg-[#FF5F57] rounded-full" />
                    <div class="size-1.5 bg-[#FEBC2D] rounded-full" />
                    <div class="size-1.5 bg-[#28C840] rounded-full" />
                  </div>
                  <div
                    class="flex items-start justify-between gap-2 p-2.5 pr-0 pb-1 min-h-[41px]"
                  >
                    <div
                      class="flex items-center flex-1 gap-1 text-xs-semibold text-ink-gray-5"
                    >
                      <img
                        v-if="logoIsImage"
                        :src="logo as string"
                        class="size-5 object-cover"
                      />
                      <component
                        :is="logo"
                        v-else-if="logo"
                        class="size-5 shrink-0 rounded"
                      />
                      <div>{{ __(name) }}</div>
                    </div>
                    <div
                      v-if="option.bars"
                      class="flex flex-col flex-1 gap-[5px]"
                    >
                      <div
                        v-for="bar in 3"
                        :key="bar"
                        class="w-full h-1.5"
                        :class="
                          pane.tone === 'light' ? 'bg-gray-100' : 'bg-gray-800'
                        "
                      />
                    </div>
                  </div>
                </div>
              </div>
            </div>
            <div class="flex items-center justify-between px-3 py-2 border-t">
              <div class="text-base text-ink-gray-7">
                {{ __(option.label) }}
              </div>
              <div
                class="rounded-full size-3.5"
                :class="
                  theme === option.value
                    ? 'border-4 border-outline-gray-7'
                    : 'border border-outline-gray-4'
                "
              />
            </div>
          </div>
        </div>
      </slot>
    </div>
  </div>
</template>

<script setup lang="ts">
import { __ } from "@/translation";
import { useTheme, type Theme } from "frappe-ui";
import { computed, type Component } from "vue";

type Pane = {
  tone: "light" | "dark";
  containerClass: string;
  screenClass: string;
};

const props = withDefaults(
  defineProps<{
    /** Controlled value. When omitted the global frappe-ui theme is used. */
    modelValue?: Theme;
    /** Brand logo shown in the previews: image URL or component. */
    logo?: string | Component;
    /** Brand name shown in the previews. */
    name?: string;
  }>(),
  { logo: "", name: "" }
);

const emit = defineEmits<{ "update:modelValue": [theme: Theme] }>();

const { currentTheme, setTheme } = useTheme();

const themeOptions: {
  value: Theme;
  label: string;
  panes: Pane[];
  bars: boolean;
}[] = [
  {
    value: "light",
    label: "Light",
    bars: true,
    panes: [
      {
        tone: "light",
        containerClass: "pl-5 pt-3.5 bg-surface-gray-2 rounded-t-[10.5px]",
        screenClass: "bg-white rounded-tl-sm",
      },
    ],
  },
  {
    value: "dark",
    label: "Dark",
    bars: true,
    panes: [
      {
        tone: "dark",
        containerClass: "pl-5 pt-3.5 bg-surface-gray-2 rounded-t-[10.5px]",
        screenClass: "bg-gray-900 rounded-tl-sm",
      },
    ],
  },
  {
    value: "system",
    label: "System",
    bars: false,
    panes: [
      {
        tone: "light",
        containerClass:
          "flex flex-1 pl-5 pt-3.5 bg-surface-gray-2 rounded-tl-[10.5px]",
        screenClass: "bg-white rounded-tl-sm w-full",
      },
      {
        tone: "dark",
        containerClass:
          "flex flex-1 pl-5 pt-3.5 bg-surface-gray-3 rounded-tr-[10.5px]",
        screenClass: "bg-gray-900 rounded-tl-sm w-full",
      },
    ],
  },
];

const logoIsImage = computed(
  () => typeof props.logo === "string" && props.logo.length > 0
);

const theme = computed<Theme>({
  get() {
    const value = props.modelValue ?? currentTheme.value;
    if (value === "light") return "light";
    if (value === "dark") return "dark";
    return "system";
  },
  set(value) {
    setTheme(value);
    emit("update:modelValue", value);
  },
});
</script>
