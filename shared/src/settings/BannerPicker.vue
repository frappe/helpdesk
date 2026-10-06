<template>
  <div class="flex flex-col gap-4">
    <div class="flex flex-col gap-1">
      <span class="text-base-medium text-ink-gray-8">{{
        __("Banner image")
      }}</span>
      <span class="text-p-sm text-ink-gray-6">{{
        __(
          "Appears behind the search bar on the knowledge base home page. Recommended size is minimum 1440x240 px in PNG or JPG."
        )
      }}</span>
    </div>
    <div
      class="flex h-28 items-center justify-center rounded-6 bg-surface-gray-1 px-4 shadow-[inset_0_0_0_1px_rgba(0,0,0,0.06)]"
      :style="{ background: previewBackground }"
    >
      <div
        class="flex h-8 w-full max-w-sm items-center gap-2 rounded-4 bg-white px-2.5 text-base text-gray-500 shadow-sm"
      >
        <LucideSearch class="size-4 shrink-0" />
        {{ __("Search articles...") }}
      </div>
    </div>
    <div class="grid grid-cols-2 gap-x-3 gap-y-4 sm:grid-cols-4">
      <FileUploader
        :fileTypes="['image/*']"
        :private="false"
        @success="(file) => save(file.file_url, '')"
      >
        <template #default="{ progress, uploading, openFileSelector }">
          <BannerOption
            :label="uploadLabel(uploading, progress)"
            :selected="Boolean(image)"
            :background="image ? imageBackground(image) : ''"
            class="border-dashed !bg-surface-base hover:!bg-surface-gray-1"
            @click="openFileSelector"
          >
            <LucideImageUp v-if="image" class="size-4 text-white" />
            <LucidePlus v-else class="size-4 text-ink-gray-5" />
          </BannerOption>
        </template>
      </FileUploader>
      <BannerOption
        :label="__('None')"
        :selected="!image && !preset"
        @click="save('', '')"
      >
        <span class="text-base text-ink-gray-5">{{ __("None") }}</span>
      </BannerOption>
      <BannerOption
        v-for="option in BANNER_PRESETS"
        :key="option.name"
        :label="presetLabel(option.name)"
        :selected="!image && preset === option.name"
        :background="option.background"
        @click="save('', option.name)"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { __ } from "../translation";
import { BANNER_PRESETS, findBannerPreset } from "../kbBanner";
import { FileUploader } from "frappe-ui";
import { computed } from "vue";
import LucideImageUp from "~icons/lucide/image-up";
import LucidePlus from "~icons/lucide/plus";
import LucideSearch from "~icons/lucide/search";
import BannerOption from "./BannerOption.vue";

const props = defineProps<{ image: string; preset: string }>();
const emit = defineEmits<{
  change: [value: { banner_image: string; banner_preset: string }];
}>();

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
  return props.image ? __("Custom image") : __("PNG or JPG, 1440×240+");
}

function presetLabel(name: string) {
  return {
    Stone: __("Stone"),
    Blue: __("Blue"),
    Green: __("Green"),
    Charcoal: __("Charcoal"),
    Navy: __("Navy"),
    Forest: __("Forest"),
  }[name];
}

function save(image: string, preset: string) {
  if (image === props.image && preset === props.preset) return;
  emit("change", { banner_image: image, banner_preset: preset });
}
</script>
