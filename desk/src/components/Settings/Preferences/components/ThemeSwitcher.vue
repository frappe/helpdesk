<template>
  <div class="flex flex-col gap-4 mt-6">
    <div class="flex flex-col gap-1">
      <slot name="title">
        <span class="text-base font-medium text-ink-gray-8">{{
          __("Theme")
        }}</span>
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
            class="flex-1 max-w-[227px] min-h-[42px] overflow-hidden rounded-lg border cursor-pointer outline-none transition-colors focus-visible:ring-2 focus-visible:ring-outline-gray-3"
            :class="
              theme === option.value
                ? 'border-outline-gray-5'
                : 'border-outline-gray-modals'
            "
            role="radio"
            :aria-checked="theme === option.value"
            tabindex="0"
            @click="theme = option.value"
            @keydown.enter.prevent="theme = option.value"
            @keydown.space.prevent="theme = option.value"
          >
            <!-- Theme-independent window mock: each frame is a fixed-tone SVG so
                 the Light/Dark/System previews always render the same regardless
                 of the app's active theme. -->
            <div :class="{ flex: option.frames.length > 1 }">
              <div
                v-for="(frame, index) in option.frames"
                :key="index"
                :class="frame.frameClass"
              >
                <div
                  class="relative"
                  :class="frame.fill ? 'w-full' : 'w-fit shrink-0'"
                >
                  <svg
                    width="207"
                    height="68"
                    viewBox="0 0 207 68"
                    fill="none"
                    xmlns="http://www.w3.org/2000/svg"
                    class="block h-auto rounded-tl-sm"
                    :class="{ 'w-full': frame.fill }"
                  >
                    <path
                      d="M0 4C0 1.79086 1.79086 0 4 0H207V83H0V4Z"
                      :fill="tones[frame.tone].background"
                    />
                    <template v-if="option.bars">
                      <rect
                        x="104"
                        y="28"
                        width="103"
                        height="6"
                        :fill="tones[frame.tone].bar"
                      />
                      <rect
                        x="104"
                        y="39"
                        width="103"
                        height="6"
                        :fill="tones[frame.tone].bar"
                      />
                      <rect
                        x="104"
                        y="50"
                        width="103"
                        height="6"
                        :fill="tones[frame.tone].bar"
                      />
                    </template>
                    <rect
                      x="4"
                      y="3"
                      width="6"
                      height="6"
                      rx="3"
                      fill="#FF5F57"
                    />
                    <rect
                      x="13"
                      y="3"
                      width="6"
                      height="6"
                      rx="3"
                      fill="#FEBC2D"
                    />
                    <rect
                      x="22"
                      y="3"
                      width="6"
                      height="6"
                      rx="3"
                      fill="#28C840"
                    />
                    <line
                      y1="13.5"
                      x2="207"
                      y2="13.5"
                      :stroke="tones[frame.tone].line"
                    />
                  </svg>
                  <div
                    class="absolute flex items-center gap-1 text-xs text-ink-gray-5 font-semibold top-[24px] left-[10px]"
                  >
                    <img
                      v-if="logoIsImage"
                      :src="logo as string"
                      class="size-5 object-cover"
                    />
                    <component
                      :is="logo"
                      v-else-if="logo"
                      class="size-5 shrink-0 rounded-[5px]"
                    />
                    <div v-if="name">{{ __(name) }}</div>
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
                    ? 'border-4 border-outline-gray-5'
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

type Tone = "light" | "dark";

type Frame = {
  tone: Tone;
  /** Stretch to fill the frame (light/dark) or natural width (system). */
  fill: boolean;
  frameClass: string;
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

// Fixed window colors per tone — independent of the active app theme.
const tones: Record<Tone, { background: string; bar: string; line: string }> = {
  light: { background: "#FFFFFF", bar: "#F3F3F3", line: "#EDEDED" },
  dark: { background: "#171717", bar: "#383838", line: "#383838" },
};

const themeOptions: {
  value: Theme;
  label: string;
  bars: boolean;
  frames: Frame[];
}[] = [
  {
    value: "light",
    label: "Light",
    bars: true,
    frames: [
      {
        tone: "light",
        fill: true,
        frameClass: "pl-5 pt-3.5 bg-surface-gray-2 rounded-t-[10.5px]",
      },
    ],
  },
  {
    value: "dark",
    label: "Dark",
    bars: true,
    frames: [
      {
        tone: "dark",
        fill: true,
        frameClass: "pl-5 pt-3.5 bg-surface-gray-2 rounded-t-[10.5px]",
      },
    ],
  },
  {
    value: "system",
    label: "System",
    bars: false,
    frames: [
      {
        tone: "light",
        fill: false,
        frameClass:
          "flex flex-1 overflow-hidden pl-5 pt-3.5 bg-surface-gray-2 rounded-tl-[10.5px] max-h-[78px]",
      },
      {
        tone: "dark",
        fill: false,
        frameClass:
          "flex flex-1 overflow-hidden pl-5 pt-3.5 bg-surface-gray-3 rounded-tr-[10.5px] max-h-[78px]",
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
