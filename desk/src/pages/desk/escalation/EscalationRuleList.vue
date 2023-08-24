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
            <IconPlus class="h-4 w-4" />
          </template>
        </Button>
      </template>
    </PageTitle>
    <ListView
      class="mt-2.5 grow"
      :columns="columns"
      :data="rules.list?.data || []"
      :empty-message="emptyMessage"
      row-key="name"
      :hide-checkbox="true"
      :hide-column-selector="true"
      :row-click="{
        type: 'action',
        fn: openDialog,
      }"
    >
      <template #is_enabled="{ data }">
        <Badge :theme="data.is_enabled ? 'green' : 'red'" variant="subtle">
          {{ data.is_enabled ? "Enabled" : "Disabled" }}
        </Badge>
      </template>
    </ListView>
    <ListNavigation :resource="rules" />
    <EscalationRuleDialog
      v-if="showDialog"
      v-model="showDialog"
      :name="selectedRule"
    />
  </div>
</template>
<script setup lang="ts">
import { ref } from "vue";
import { usePageMeta, Badge } from "frappe-ui";
import { socket } from "@/socket";
import { createListManager } from "@/composables/listManager";
import { ListView } from "@/components";
import ListNavigation from "@/components/ListNavigation.vue";
import PageTitle from "@/components/PageTitle.vue";
import EscalationRuleDialog from "./EscalationRuleDialog.vue";
import IconPlus from "~icons/lucide/plus";

const showDialog = ref(false);
const selectedRule = ref(null);
const emptyMessage = "No Escalation Rules Found";
const columns = [
  {
    title: "Priority",
    key: "priority",
    width: "w-1/3",
  },
  {
    title: "Team",
    key: "team",
    width: "w-1/3",
  },
  {
    title: "Ticket type",
    key: "ticket_type",
    width: "w-1/3",
  },
  {
    title: "",
    key: "is_enabled",
    width: "w-20 flex justify-end",
  },
];

const rules = createListManager({
  doctype: "HD Escalation Rule",
  fields: ["name", "priority", "team", "ticket_type", "is_enabled"],
  auto: true,
});

usePageMeta(() => {
  return {
    title: "Escalation rules",
  };
});

function openDialog(rule: string | null) {
  selectedRule.value = rule;
  showDialog.value = true;
}

socket.on("helpdesk:new-escalation-rule", () => rules.reload());
socket.on("helpdesk:delete-escalation-rule", () => rules.reload());
</script>
