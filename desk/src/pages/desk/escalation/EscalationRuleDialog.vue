<template>
  <Dialog :options="options">
    <template #body-content>
      <div class="space-y-4">
        <EscalationRuleDialogFieldList
          v-model:doc="doc"
          title="Criteria"
          :items="criteria"
        />
        <EscalationRuleDialogFieldList
          v-model:doc="doc"
          title="Actions"
          :items="actions"
        />
      </div>
    </template>
  </Dialog>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { createResource, createDocumentResource, Dialog } from "frappe-ui";
import { createToast } from "@/utils";
import { useError } from "@/composables/error";
import EscalationRuleDialogFieldList from "./EscalationRuleDialogFieldList.vue";

const props = defineProps({
  name: {
    type: String,
    required: true,
  },
});

const rule = createDocumentResource({
  doctype: "HD Escalation Rule",
  name: props.name || 747,
  fields: ["name", "priority", "team", "to_team", "to_agent", "to_priority"],
  auto: true,
  onError() {
    rule.doc = {};
  },
  setValue: {
    debounce: 3000,
    onSuccess() {
      createToast({
        title: "Rule updated",
        icon: "check",
        iconClasses: "text-green-500",
      });
    },
    onError: useError({ title: "Error updating rule" }),
  },
  delete: {
    onSuccess() {
      createToast({
        title: "Rule deleted",
        icon: "check",
        iconClasses: "text-green-500",
      });
    },
    onError: useError({ title: "Error deleting rule" }),
  },
});

const newRule = createResource({
  url: "frappe.client.insert",
  onSuccess(data) {
    createToast({
      title: "Rule created",
      icon: "check",
      iconClasses: "text-green-500",
    });

    rule.name = data.name;
    rule.reload();
  },
  onError: useError({ title: "Error creating rule" }),
});

const doc = computed({
  get() {
    return rule.doc || {};
  },
  set(doc) {
    rule.doc = doc;
  },
});
const isNew = computed(() => !doc.value.name);

function save() {
  const d = {
    is_enabled: doc.value.is_enabled,
    priority: doc.value.priority,
    team: doc.value.team,
    ticket_type: doc.value.ticket_type,
    to_agent: doc.value.to_agent,
    to_priority: doc.value.to_priority,
    to_team: doc.value.to_team,
    to_ticket_type: doc.value.to_ticket_type,
  };

  if (doc.value.name) {
    rule.setValue.submit(d);
    return;
  }

  newRule.submit({
    doc: {
      doctype: "HD Escalation Rule",
      ...d,
    },
  });
}

const options = computed(() => ({
  title: isNew.value ? "New rule" : "Edit rule",
  actions: [
    {
      label: isNew.value ? "Create" : "Save",
      theme: "gray",
      variant: "subtle",
      onClick: () => save(),
    },
    {
      label: doc.value?.is_enabled ? "Disable" : "Enable",
      theme: doc.value?.is_enabled ? "red" : "green",
      variant: "subtle",
      onClick: () =>
        rule.setValue.submit({ is_enabled: !doc.value.is_enabled }),
      hidden: isNew.value,
    },
    {
      label: "Delete",
      theme: "red",
      variant: "subtle",
      onClick: () => rule.delete.submit(),
      hidden: isNew.value,
    },
  ].filter((action) => !action.hidden),
}));

const criteria = [
  {
    label: "Priority is",
    doctype: "HD Ticket Priority",
    key: "priority",
  },
  {
    label: "Team is",
    doctype: "HD Team",
    key: "team",
  },
  {
    label: "Ticket type is",
    doctype: "HD Ticket Type",
    key: "ticket_type",
  },
];

const actions = [
  {
    label: "Change priority to",
    doctype: "HD Ticket Priority",
    key: "to_priority",
  },
  {
    label: "Change team to",
    doctype: "HD Team",
    key: "to_team",
  },
  {
    label: "Change ticket type to",
    doctype: "HD Ticket Type",
    key: "to_ticket_type",
  },
  {
    label: "Assign to",
    doctype: "HD Agent",
    key: "to_agent",
  },
];
</script>
