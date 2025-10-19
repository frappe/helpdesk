<template>
  <CannedResponseList v-if="cannedResponseActiveScreen.screen == 'list'" />
  <CannedResponseView v-else-if="cannedResponseActiveScreen.screen == 'view'" />
</template>

<script setup lang="ts">
import { createListResource } from "frappe-ui";
import CannedResponseList from "./CannedResponseList.vue";
import CannedResponseView from "./CannedResponseView.vue";
import { provide, ref } from "vue";

const cannedResponseActiveScreen = ref({
  screen: "list",
  data: null,
});
const cannedResponseSearchQuery = ref("");

const cannedResponseListData = createListResource({
  doctype: "Email Template",
  fields: ["name", "subject", "response", "teams"],
  filters: {
    reference_doctype: "HD Ticket",
  },
  orderBy: "modified desc",
  start: 0,
  pageLength: 999,
  auto: true,
});

provide("cannedResponseActiveScreen", cannedResponseActiveScreen);
provide("cannedResponseSearchQuery", cannedResponseSearchQuery);
provide("cannedResponseListData", cannedResponseListData);
</script>
