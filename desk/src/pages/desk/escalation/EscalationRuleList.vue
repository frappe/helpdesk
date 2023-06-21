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
    <HelpdeskTable
      class="grow"
      :columns="columns"
      :data="rules.list?.data || []"
      row-key="name"
      :emit-row-click="true"
      :hide-checkbox="true"
      :hide-column-selector="true"
      @row-click="openDialog"
    >
      <template #is_enabled="{ data }">
        <Badge :theme="data.is_enabled ? 'green' : 'red'" variant="subtle">
          {{ data.is_enabled ? "Enabled" : "Disabled" }}
        </Badge>
      </template>
    </HelpdeskTable>
    <ListNavigation class="p-3" v-bind="rules" />
    <EscalationRuleDialog
      v-if="showDialog"
      v-model="showDialog"
      :name="selectedRule"
    />
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

const showDialog = ref(false);
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
    title: "Ticket type",
    colKey: "ticket_type",
    colClass: "w-1/3",
  },
  {
    title: "",
    colKey: "is_enabled",
    colClass: "w-20 flex justify-end",
  },
];

const rules = createListManager({
  doctype: "HD Escalation Rule",
  fields: ["name", "priority", "team", "ticket_type", "is_enabled"],
  auto: true,
});

function openDialog(rule: string | null) {
  selectedRule.value = rule;
  showDialog.value = true;
}

socket.on("helpdesk:new-escalation-rule", () => rules.reload());
socket.on("helpdesk:delete-escalation-rule", () => rules.reload());
</script>
