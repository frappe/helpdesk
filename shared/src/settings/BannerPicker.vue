<template>
  <div class="flex flex-col gap-4">
    <div class="flex flex-col gap-1">
      <span class="text-base-medium text-ink-gray-8">{{
        __("Banner")
      }}</span>
      <span class="text-p-sm text-ink-gray-6">{{
        __(
          "Choose a color, pattern or image to show behind the search bar on the knowledge base home page. Recommended image size is minimum 1440x240 px in PNG or JPG."
        )
      }}</span>
    </div>
    <div
      class="flex h-28 items-center justify-center rounded-6 border border-outline-gray-1 px-4"
      :style="{ background: previewBackground }"
    >
      <div
        class="flex h-8 w-full max-w-sm items-center gap-2 rounded-4 border border-outline-gray-1 bg-surface-base px-2.5 text-base text-ink-gray-4 shadow-sm"
      >
        <LucideSearch class="size-4 shrink-0" />
        {{ __("Search articles...") }}
      </div>
    </div>
    <div class="flex flex-wrap items-center justify-between gap-3">
      <div class="flex items-center gap-2" role="radiogroup">
        <Tooltip :text="__('None')">
          <button
            type="button"
            role="radio"
            :aria-label="__('None')"
            :aria-checked="!image && !preset"
            :class="[swatch, ring(!image && !preset)]"
            class="flex items-center justify-center bg-surface-base text-ink-gray-4"
            @click="save('', '')"
          >
            <LucideBan class="size-4" />
          </button>
        </Tooltip>
        <Tooltip
          v-for="option in BANNER_PRESETS"
          :key="option.name"
          :text="presetLabel(option.name)"
        >
          <button
            type="button"
            role="radio"
            :aria-label="presetLabel(option.name)"
            :aria-checked="!image && preset === option.name"
            :class="[swatch, ring(!image && preset === option.name)]"
            :style="{ background: option.background }"
            @click="save('', option.name)"
          />
        </Tooltip>
        <Tooltip v-if="image" :text="__('Custom image')">
          <span
            role="radio"
            :aria-label="__('Custom image')"
            aria-checked="true"
            :class="[swatch, ring(true)]"
            :style="{ background: imageBackground(image) }"
          />
        </Tooltip>
      </div>
      <FileUploader
        :fileTypes="['image/*']"
        :private="false"
        @success="(file) => save(file.file_url, '')"
      >
        <template #default="{ progress, uploading, openFileSelector }">
          <Button
            variant="subtle"
            icon-left="lucide-image-up"
            :label="uploadLabel(uploading, progress)"
            :loading="uploading"
            @click="openFileSelector"
          />
        </template>
      </FileUploader>
    </div>
  </div>
</template>

<script setup lang="ts">
import { __ } from "../translation";
import { BANNER_PRESETS, findBannerPreset } from "../kbBanner";
import { Button, FileUploader, Tooltip } from "frappe-ui";
import { computed } from "vue";
import LucideBan from "~icons/lucide/ban";
import LucideSearch from "~icons/lucide/search";

const props = defineProps<{ image: string; preset: string }>();
const emit = defineEmits<{
  change: [value: { banner_image: string; banner_preset: string }];
}>();

const swatch =
  "size-8 shrink-0 rounded-[8px] border [--banner-pattern-scale:0.4] border-outline-gray-2 outline outline-2 outline-offset-2 transition-[outline-color]";

function ring(selected: boolean) {
  return selected
    ? "outline-[--ink-gray-9]"
    : "outline-transparent hover:outline-[--outline-gray-3]";
}

const previewBackground = computed(() =>
  props.image
    ? imageBackground(props.image)
    : findBannerPreset(props.preset)?.background || ""
);

function imageBackground(url: string) {
  return `center / cover url('${url}')`;
}

function uploadLabel(uploading: boolean, progress: number) {
  if (uploading) return __("Uploading {0}%", [progress]);
  return props.image ? __("Replace image") : __("Upload image");
}

function presetLabel(name: string) {
  return {
    Gray: __("Gray"),
    Blue: __("Blue"),
    Violet: __("Violet"),
    Lines: __("Lines"),
  }[name];
}

function save(image: string, preset: string) {
  if (image === props.image && preset === props.preset) return;
  emit("change", { banner_image: image, banner_preset: preset });
}
</script>
