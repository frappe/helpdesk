<template>
  <div class="flex flex-col">
    <PageTitle title="Escalation Rules">
      <template #right>
        <Button
          label="New rule"
          theme="gray"
          variant="solid"
          @click="isDialogVisible = !isDialogVisible"
        >
          <template #prefix>
            <IconPlus class="h-4 w-4" />
          </template>
        </Button>
      </template>
    </PageTitle>
    <HelpdeskTable
      class="grow"
      :columns="columns"
      :data="rules.list?.data || []"
      row-key="name"
      :emit-row-click="true"
      :hide-checkbox="true"
      :hide-column-selector="true"
      @row-click="openRule"
    >
      <template #is_enabled="{ data }">
        <Badge :theme="data.is_enabled ? 'green' : 'orange'" variant="subtle">
          {{ data.is_enabled ? "Enabled" : "Disabled" }}
        </Badge>
      </template>
    </HelpdeskTable>
    <ListNavigation class="p-3" v-bind="rules" />
    <span v-if="showRule">
      <EscalationRuleDialog v-model="showRule" :name="selectedRule" />
    </span>
  </div>
</template>
<script setup lang="ts">
import { ref } from "vue";
import { Badge } from "frappe-ui";
import { socket } from "@/socket";
import { createListManager } from "@/composables/listManager";
import HelpdeskTable from "@/components/HelpdeskTable.vue";
import ListNavigation from "@/components/ListNavigation.vue";
import PageTitle from "@/components/PageTitle.vue";
import EscalationRuleDialog from "./EscalationRuleDialog.vue";
import IconPlus from "~icons/lucide/plus";

const isDialogVisible = ref(false);
const showRule = ref(false);
const selectedRule = ref(null);
const columns = [
  {
    title: "Priority",
    colKey: "priority",
    colClass: "w-1/3",
  },
  {
    title: "Team",
    colKey: "team",
    colClass: "w-1/3",
  },
  {
    title: "Status",
    colKey: "is_enabled",
    colClass: "w-1/3",
  },
];

const rules = createListManager({
  doctype: "HD Escalation Rule",
  fields: ["name", "priority", "team", "is_enabled"],
  auto: true,
});

function openRule(id: string) {
  selectedRule.value = id;
  showRule.value = true;
}

socket.on("helpdesk:new-escalation-rule", () => {
  if (!rules.hasPreviousPage) rules.reload();
});
</script>
