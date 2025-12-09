<template>
  <SavedRepliesList v-if="savedRepliesActiveScreen.screen == 'list'" />
  <SavedReplyView v-else-if="savedRepliesActiveScreen.screen == 'view'" />
</template>

<script setup lang="ts">
import { createListResource } from "frappe-ui";
import SavedRepliesList from "./SavedRepliesList.vue";
import SavedReplyView from "./SavedReplyView.vue";
import { onUnmounted, provide, ref } from "vue";
import { SavedReplyListResourceSymbol } from "../../../types";

const savedRepliesActiveScreen = ref({
  screen: "list",
  data: null,
});
const savedRepliesSearchQuery = ref("");

const savedReplyListResource = createListResource({
  doctype: "HD Saved Reply",
  fields: ["name", "title", "owner", "scope"],
  cache: ["SavedReplyList"],
  auto: true,
  orderBy: "modified desc",
  start: 0,
  pageLength: 999,
});

provide(SavedReplyListResourceSymbol, savedReplyListResource);
provide("savedRepliesActiveScreen", savedRepliesActiveScreen);
provide("savedRepliesSearchQuery", savedRepliesSearchQuery);

onUnmounted(() => {
  savedRepliesSearchQuery.value = "";
  savedReplyListResource.filters = {};
});
</script>
