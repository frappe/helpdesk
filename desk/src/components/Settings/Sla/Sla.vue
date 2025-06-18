<template>
  <div>
    <SlaPolicies v-if="activeScreen.screen == 'list'" />
    <SlaPolicyView v-else-if="activeScreen.screen == 'view'" />
  </div>
</template>

<script setup lang="ts">
import { activeScreen, slaPolicyListData } from "./sla";
import SlaPolicies from "./SlaPolicies.vue";
import SlaPolicyView from "./SlaPolicyView.vue";
import { onMounted } from "vue";

onMounted(() => {
  slaPolicyListData.fetch();
});
</script>
