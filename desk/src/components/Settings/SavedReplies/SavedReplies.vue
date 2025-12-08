<template>
  <SavedRepliesList v-if="savedRepliesActiveScreen.screen == 'list'" />
  <SavedReplyView v-else-if="savedRepliesActiveScreen.screen == 'view'" />
</template>

<script setup lang="ts">
import SavedRepliesList from "./SavedRepliesList.vue";
import SavedReplyView from "./SavedReplyView.vue";
import { provide, ref } from "vue";

const savedRepliesActiveScreen = ref({
  screen: "list",
  data: null,
});
const savedRepliesSearchQuery = ref("");

provide("savedRepliesActiveScreen", savedRepliesActiveScreen);
provide("savedRepliesSearchQuery", savedRepliesSearchQuery);
</script>
