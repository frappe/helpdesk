<template>
  <Dialog :options="options">
    <template #body-main>
      <div class="space-y-4 px-6 pt-6 text-base">
        <Input v-model="isEnabled" type="checkbox" label="Enabled" />
        <div class="text-lg font-medium text-gray-900">Apply rule if</div>
        <div class="flex flex-wrap items-center gap-2">
          <div class="flex items-center gap-2">
            <div class="text-gray-800">Priority is</div>
            <SearchComplete
              doctype="HD Ticket Priority"
              placeholder="Any"
              :value="priority"
              @change="(v) => (priority = v.value)"
            />
          </div>
          <div class="text-gray-600">and</div>
          <div class="flex items-center gap-2">
            <div class="text-gray-800">Team is</div>
            <SearchComplete
              doctype="HD Team"
              placeholder="Any"
              :value="team"
              @change="(v) => (team = v.value)"
            />
          </div>
        </div>
        <div class="text-lg font-medium text-gray-900">Do these</div>
        <div class="flex flex-wrap items-center gap-2">
          <div class="flex items-center gap-2">
            <div class="text-gray-800">Change priority to</div>
            <SearchComplete
              doctype="HD Ticket Priority"
              placeholder="Any"
              :value="toPriority"
              @change="(v) => (toPriority = v.value)"
            />
          </div>
          <div class="text-gray-600">and</div>
          <div class="flex items-center gap-2">
            <div class="text-gray-800">Change team to</div>
            <SearchComplete
              doctype="HD Team"
              placeholder="Any"
              :value="toTeam"
              @change="(v) => (toTeam = v.value)"
            />
          </div>
          <div class="text-gray-600">and</div>
          <div class="flex items-center gap-2">
            <div class="text-gray-800">Assign to</div>
            <SearchComplete
              doctype="HD Agent"
              placeholder="Any"
              :value="toAgent"
              @change="(v) => (toAgent = v.value)"
            />
          </div>
        </div>
      </div>
    </template>
  </Dialog>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { createDocumentResource, Dialog, Input } from "frappe-ui";
import { createToast } from "@/utils/toasts";
import SearchComplete from "@/components/SearchComplete.vue";

const props = defineProps({
  name: {
    type: String,
    required: true,
  },
});

const priority = computed({
  get() {
    return rule.doc?.priority;
  },
  set(priority: string) {
    rule.doc.priority = priority;
  },
});
const team = computed({
  get() {
    return rule.doc?.team;
  },
  set(team: string) {
    rule.doc.team = team;
  },
});
const toPriority = computed({
  get() {
    return rule.doc?.to_priority;
  },
  set(priority: string) {
    rule.doc.to_priority = priority;
  },
});
const toTeam = computed({
  get() {
    return rule.doc?.to_team;
  },
  set(team: string) {
    rule.doc.to_team = team;
  },
});
const toAgent = computed({
  get() {
    return rule.doc?.to_agent;
  },
  set(team: string) {
    rule.doc.to_agent = team;
  },
});
const isEnabled = computed({
  get() {
    return rule.doc?.is_enabled;
  },
  set(enabled: boolean) {
    rule.doc.is_enabled = enabled;
  },
});

const rule = createDocumentResource({
  doctype: "HD Escalation Rule",
  name: props.name,
  fields: ["name", "priority", "team", "to_team", "to_agent", "to_priority"],
  auto: true,
  setValue: {
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

const options = computed(() => ({
  title: rule.doc?.name,
  actions: [
    {
      label: "Save",
      theme: "gray",
      variant: "subtle",
      disabled: !rule.doc?.priority && !rule.doc?.team,
      onClick: () =>
        rule.setValue.submit({
          is_enabled: isEnabled.value,
          priority: priority.value,
          team: team.value,
          to_agent: toAgent.value,
          to_priority: toPriority.value,
          to_team: toTeam.value,
        }),
    },
    {
      label: "Delete",
      theme: "red",
      variant: "subtle",
      onClick: () => rule.delete.submit(),
    },
  ],
}));
</script>
