<template>
  <AssignmentRulesList v-if="assignmentRulesActiveScreen.screen === 'list'" />
  <AssignmentRuleView v-if="assignmentRulesActiveScreen.screen === 'view'" />
</template>

<script setup lang="ts">
import { provide, ref } from "vue";
import { assignmentRulesActiveScreen } from "@/stores/assignmentRules";
import AssignmentRulesList from "./AssignmentRulesList.vue";
import AssignmentRuleView from "./AssignmentRuleView.vue";

const assignmentRuleSearchQuery = ref("");

provide("assignmentRuleSearchQuery", assignmentRuleSearchQuery);
</script>
