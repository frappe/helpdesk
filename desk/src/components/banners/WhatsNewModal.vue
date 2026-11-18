<template>
  <BottomSheet v-if="isMobileView" v-model:open="isOpen" :title="title">
    <WhatsNewReleases class="px-4 pb-8" :releases="releases" />
  </BottomSheet>
  <Dialog v-else v-model:open="isOpen" :title="title" size="2xl">
    <template #default>
      <WhatsNewReleases
        class="max-h-[70vh] overflow-y-auto"
        :releases="releases"
      />
    </template>
  </Dialog>
</template>

<script setup lang="ts">
import WhatsNewReleases from "@/components/banners/WhatsNewReleases.vue";
import { useScreenSize } from "@/composables/screen";
import { useWhatsNewModal } from "@/composables/useWhatsNewModal";
import { __ } from "@/translation";
import { BottomSheet, Dialog } from "frappe-ui";

const { isOpen, releases } = useWhatsNewModal();
const { isMobileView } = useScreenSize();
const title = __("What's new");
</script>
