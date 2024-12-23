<template>
  <div class="flex flex-col">
    <PageTitle title="Escalation Rules">
      <template #right>
        <Button
          label="New rule"
          theme="gray"
          variant="solid"
          @click="openDialog(null)"
        >
          <template #prefix>
            <LucidePlus class="h-4 w-4" />
          </template>
        </Button>
      </template>
    </PageTitle>
    <div class="my-2" />
    <ListViewBuilder
      :options="{
        doctype: 'HD Escalation Rule',
        hideViewControls: true,
        selectable: false,
      }"
      @row-click="openDialog"
    />
    <EscalationRuleDialog
      v-if="showDialog"
      v-model="showDialog"
      :name="selectedRule"
    />
  </div>
</template>
<script setup lang="ts">
import { ref } from "vue";
import { usePageMeta } from "frappe-ui";
import PageTitle from "@/components/PageTitle.vue";
import EscalationRuleDialog from "./EscalationRuleDialog.vue";
import ListViewBuilder from "@/components/ListViewBuilder.vue";

const showDialog = ref(false);
const selectedRule = ref(null);

usePageMeta(() => {
  return {
    title: "Escalation rules",
  };
});

function openDialog(rule: string | null) {
  selectedRule.value = rule;
  showDialog.value = true;
}
</script>
