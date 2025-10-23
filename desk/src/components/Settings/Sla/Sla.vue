<template>
  <SlaPolicies v-if="slaActiveScreen.screen == 'list'" />
  <SlaPolicyView v-else-if="slaActiveScreen.screen == 'view'" />
</template>

<script setup lang="ts">
import { slaActiveScreen } from "@/stores/sla";
import SlaPolicies from "./SlaPolicies.vue";
import SlaPolicyView from "./SlaPolicyView.vue";
import { createListResource } from "frappe-ui";
import { provide, ref } from "vue";

const slaPolicyListData = createListResource({
  doctype: "HD Service Level Agreement",
  fields: ["name", "default_sla", "enabled", "description"],
  cache: ["SLAPolicyList"],
  orderBy: "creation desc",
  start: 0,
  pageLength: 999,
  auto: true,
});
const slaSearchQuery = ref("");

provide("slaSearchQuery", slaSearchQuery);
provide("slaPolicyList", slaPolicyListData);
</script>
