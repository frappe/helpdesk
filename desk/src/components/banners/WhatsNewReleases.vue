<template>
  <div class="flex flex-col gap-8">
    <section v-for="release in releases" :key="release.version ?? 'next'">
      <div
        class="mb-4 flex items-baseline gap-2 border-b border-outline-gray-1 pb-2"
      >
        <h2 class="text-lg font-semibold text-ink-gray-9">
          {{ release.version ? `v${release.version}` : __("Next release") }}
        </h2>
        <span v-if="release.date" class="text-p-sm text-ink-gray-5">
          {{ dayjsLocal(release.date).format("D MMM YYYY") }}
        </span>
      </div>
      <article
        v-for="note in release.notes"
        :key="note.id"
        class="mb-6 flex flex-col gap-3 last:mb-0"
      >
        <h3 class="text-base font-semibold text-ink-gray-9">
          {{ note.title }}
        </h3>
        <template v-if="note.media">
          <video
            v-if="note.media.kind === 'video'"
            :src="mediaUrl(note.media)"
            class="w-full rounded-lg border border-outline-gray-1"
            autoplay
            loop
            muted
            playsinline
          />
          <img
            v-else
            :src="mediaUrl(note.media)"
            :alt="note.title"
            class="w-full rounded-lg border border-outline-gray-1"
            loading="lazy"
          />
        </template>
        <!-- The HTML is rendered on the server from Markdown files shipped in the app -->
        <div class="prose-f text-ink-gray-7" v-html="note.body" />
      </article>
    </section>
  </div>
</template>

<script setup lang="ts">
import type { WhatsNewMedia, WhatsNewRelease } from "@/composables/useBanners";
import { __ } from "@/translation";
import { dataTheme } from "@/utils";
import { dayjsLocal } from "frappe-ui";

defineProps<{ releases: WhatsNewRelease[] }>();

function mediaUrl(media: WhatsNewMedia) {
  return dataTheme.value === "dark" && media.dark_url
    ? media.dark_url
    : media.url;
}
</script>
