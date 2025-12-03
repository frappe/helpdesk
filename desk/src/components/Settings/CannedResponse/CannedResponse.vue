<template>
  <CannedResponseList v-if="cannedResponseActiveScreen.screen == 'list'" />
  <CannedResponseView v-else-if="cannedResponseActiveScreen.screen == 'view'" />
</template>

<script setup lang="ts">
import CannedResponseList from "./CannedResponseList.vue";
import CannedResponseView from "./CannedResponseView.vue";
import { provide, ref } from "vue";

const cannedResponseActiveScreen = ref({
  screen: "list",
  data: null,
});
const cannedResponseSearchQuery = ref("");

provide("cannedResponseActiveScreen", cannedResponseActiveScreen);
provide("cannedResponseSearchQuery", cannedResponseSearchQuery);
</script>
