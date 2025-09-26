<template>
  <div class="border-b px-2 sm:px-4 py-2 flex items-center">
    <div v-if="isMobileView">
      <Button
        variant="ghost"
        icon="menu"
        @click="mobileSidebarOpened = !mobileSidebarOpened"
      />
    </div>
    <Breadcrumbs :items="routes" />
  </div>
</template>

<script setup lang="ts">
import { mobileSidebarOpened } from "@/composables/mobile";
import { useScreenSize } from "@/composables/screen";
import { Breadcrumbs, Button } from "frappe-ui";
import { RouterLinkProps } from "vue-router";

const { isMobileView } = useScreenSize();

defineProps({
  routes: {
    type: Array as () => {
      label: string;
      route?: RouterLinkProps["to"];
      onClick?: () => void;
      [key: string]: any;
    }[],
    required: true,
  },
});
</script>
