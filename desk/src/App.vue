<template>
  <span class="fixed inset-0">
    <RouterView class="antialiased" />
    <Toasts />
    <Toaster position="top-right" rich-colors />
    <KeymapDialog />
  </span>
</template>

<script setup lang="ts">
import { provide, ref, onMounted } from 'vue';
import { Toasts } from 'frappe-ui';
import { Toaster } from 'vue-sonner';
import { createToast } from '@/utils';
import { useConfigStore } from '@/stores/config';
import KeymapDialog from '@/pages/KeymapDialog.vue';

useConfigStore();

const viewportWidth = ref(
  Math.max(document.documentElement.clientWidth || 0, window.innerWidth || 0)
);

provide('viewportWidth', viewportWidth);

onMounted(async () => {
  window.addEventListener('online', () => {
    createToast({
      title: 'You are now online',
      type: 'success',
    });
  });

  window.addEventListener('offline', () => {
    createToast({
      title: 'You are now offline',
      type: 'warning',
    });
  });
});
</script>
