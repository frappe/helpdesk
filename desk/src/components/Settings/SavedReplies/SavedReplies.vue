<template>
  <SavedRepliesList v-if="savedRepliesActiveScreen.screen == 'list'" />
  <SavedRepliesView v-else-if="savedRepliesActiveScreen.screen == 'view'" />
</template>

<script setup lang="ts">
import SavedRepliesList from "./SavedRepliesList.vue";
import SavedRepliesView from "./SavedRepliesView.vue";
import { provide, ref } from "vue";

const savedRepliesActiveScreen = ref({
  screen: "list",
  data: null,
});
const savedRepliesSearchQuery = ref("");

provide("savedRepliesActiveScreen", savedRepliesActiveScreen);
provide("savedRepliesSearchQuery", savedRepliesSearchQuery);
</script>
