<template>
  <div
    v-if="assignmentRulesListData.loading && !assignmentRulesListData.data"
    class="flex items-center justify-center mt-12"
  >
    <LoadingIndicator class="w-4" />
  </div>
  <div v-else class="-ml-2 grow">
    <div
      v-if="!assignmentRulesListData.loading && !assignmentRulesList?.length"
      class="flex flex-col items-center justify-center gap-4 h-full"
    >
      <div
        class="p-4 size-14.5 rounded-full bg-surface-gray-1 flex justify-center items-center"
      >
        <Settings class="size-6 text-ink-gray-6 rotate-90" />
      </div>
      <div class="flex flex-col items-center gap-1">
        <div class="text-base font-medium text-ink-gray-6">
          {{ __("No assignment rule found") }}
        </div>
        <div class="text-p-sm text-ink-gray-5 max-w-60 text-center">
          {{ __("Add one to get started.") }}
        </div>
      </div>
      <Button
        :label="__('New')"
        variant="outline"
        icon-left="plus"
        @click="goToNew()"
      />
    </div>
    <div v-else>
      <div class="grid grid-cols-12 items-center gap-4 text-sm text-gray-600">
        <div class="col-span-7 ml-2">{{ __("Assignment rule") }}</div>
        <div class="col-span-3">{{ __("Priority") }}</div>
        <div class="col-span-2">{{ __("Enabled") }}</div>
      </div>
      <hr class="mt-2 mx-2" />
      <div
        v-for="(assignmentRule, index) in assignmentRulesList"
        :key="assignmentRule.name"
      >
        <AssignmentRuleListItem :data="assignmentRule" />
        <hr v-if="index !== assignmentRulesList.length - 1" class="mx-2" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { LoadingIndicator } from "frappe-ui";
import { inject, Ref, ref, watch } from "vue";
import AssignmentRuleListItem from "./AssignmentRuleListItem.vue";
import {
  assignmentRulesActiveScreen,
  resetAssignmentRuleData,
} from "@/stores/assignmentRules";
import Settings from "~icons/lucide/settings-2";
import { AssignmentRuleListResourceSymbol } from "@/types";

const assignmentRulesListData = inject(AssignmentRuleListResourceSymbol);

const assignmentRulesList = ref(assignmentRulesListData.data || []);

const assignmentRuleSearchQuery = inject<Ref>("assignmentRuleSearchQuery");

const goToNew = () => {
  resetAssignmentRuleData();
  assignmentRulesActiveScreen.value = {
    screen: "view",
    data: null,
  };
};

watch(
  () => [assignmentRuleSearchQuery.value, assignmentRulesListData.data],
  ([query, data]) => {
    if (!query) {
      assignmentRulesList.value = data || [];
      return;
    }
    assignmentRulesList.value =
      data?.filter((item) => {
        return (
          item.name.toLowerCase().includes(query.toLowerCase()) ||
          item.description.toLowerCase().includes(query.toLowerCase())
        );
      }) || [];
  }
);
</script>
