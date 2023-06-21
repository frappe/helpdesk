<template>
  <Dialog :options="options">
    <template #body-content>
      <div class="space-y-4 text-base">
        <div class="text-lg font-medium text-gray-900">Criteria</div>
        <div class="flex flex-wrap items-center gap-2">
          <div
            v-for="(criterion, index) in criteria"
            :key="criterion.key"
            class="flex items-center gap-2"
          >
            <div class="text-gray-800">{{ criterion.label }}</div>
            <SearchComplete
              placeholder="Any"
              :doctype="criterion.doctype"
              :value="doc[criterion.key]"
              @change="(v) => (doc[criterion.key] = v.value)"
            />
            <span v-if="index + 1 < criteria.length" class="text-gray-600">
              and
            </span>
          </div>
        </div>
        <div class="text-lg font-medium text-gray-900">Actions</div>
        <div class="flex flex-wrap items-center gap-2">
          <div
            v-for="(action, index) in actions"
            :key="action.key"
            class="flex items-center gap-2"
          >
            <div class="text-gray-800">{{ action.label }}</div>
            <SearchComplete
              placeholder="Any"
              :doctype="action.doctype"
              :value="doc[action.key]"
              @change="(v) => (doc[action.key] = v.value)"
            />
            <span v-if="index + 1 < actions.length" class="text-gray-600">
              and
            </span>
          </div>
        </div>
      </div>
    </template>
  </Dialog>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { createResource, createDocumentResource, Dialog } from "frappe-ui";
import { createToast } from "@/utils/toasts";
import SearchComplete from "@/components/SearchComplete.vue";

const props = defineProps({
  name: {
    type: String,
    required: false,
    default: "",
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
    onError(error) {
      createToast({
        title: "Error updating rule",
        text: error.messages.join(", "),
        icon: "x",
        iconClasses: "text-red-500",
      });
    },
  },
  delete: {
    onSuccess() {
      createToast({
        title: "Rule deleted",
        icon: "check",
        iconClasses: "text-green-500",
      });
    },
    onError(error) {
      createToast({
        title: "Error deleting rule",
        text: error.messages.join(", "),
        icon: "x",
        iconClasses: "text-red-500",
      });
    },
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
  onError(error) {
    createToast({
      title: "Error creating rule",
      text: error.messages.join(", "),
      icon: "x",
      iconClasses: "text-red-500",
    });
  },
});

const doc = computed(() => rule.doc || {});
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
