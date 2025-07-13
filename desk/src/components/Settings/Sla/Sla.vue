<template>
  <div class="pb-8">
    <SlaPolicies v-if="slaActiveScreen.screen == 'list'" />
    <SlaPolicyView v-else-if="slaActiveScreen.screen == 'view'" />
  </div>
</template>

<script setup lang="ts">
import { slaActiveScreen } from "@/stores/sla";
import SlaPolicies from "./SlaPolicies.vue";
import SlaPolicyView from "./SlaPolicyView.vue";
</script>
