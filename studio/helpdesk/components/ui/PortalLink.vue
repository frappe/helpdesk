<template>
  <!-- A real link: new tab, copy link and crawlers work, unlike a click handler. -->
  <RouterLink :to="to"><slot /></RouterLink>
</template>

<script setup lang="ts">
import { RouterLink, type RouteLocationRaw } from "vue-router";

defineOptions({ name: "PortalLink" });

defineProps<{ to: RouteLocationRaw }>();
</script>
