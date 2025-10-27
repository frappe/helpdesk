<template>
  <SettingsLayoutBase>
    <template #title>
      <div class="flex items-center gap-2">
        <Button
          variant="ghost"
          icon-left="chevron-left"
          :label="teamData.name || __('New Team')"
          size="md"
          @click="goBack()"
          class="cursor-pointer -ml-4 hover:bg-transparent focus:bg-transparent focus:outline-none focus:ring-0 focus:ring-offset-0 focus-visible:none active:bg-transparent active:outline-none active:ring-0 active:ring-offset-0 active:text-ink-gray-5 font-semibold text-ink-gray-7 text-lg hover:opacity-70 !pr-0"
        />
        <Badge
          variant="subtle"
          theme="orange"
          size="sm"
          :label="__('Unsaved changes')"
          v-if="isDirty"
        />
      </div>
    </template>
    <template #actions>
      <Button
        :label="__('Save')"
        variant="solid"
        @click="saveTeam()"
        :disabled="!isDirty"
        :loading="teamsList.insert.loading"
      />
    </template>
    <template #content>
      <div class="flex flex-col gap-4">
        <div class="space-y-1.5">
          <FormControl
            v-model="teamData.name"
            :label="__('Team Name')"
            :placeholder="__('Product Experts')"
            maxlength="50"
            required
            @change="validateData('name')"
          />
          <ErrorMessage :message="errors.name" />
        </div>
        <div class="flex flex-col gap-1.5">
          <FormLabel :label="__('Members')" required />
          <div class="flex">
            <AgentSelector
              v-model="teamData.agents"
              @change="validateData('agents')"
            />
          </div>
          <ErrorMessage :message="errors.agents" />
        </div>
      </div>
    </template>
  </SettingsLayoutBase>
</template>

<script setup lang="ts">
import { computed, inject, onMounted, ref } from "vue";
import SettingsLayoutBase from "../SettingsLayoutBase.vue";
import { Badge, ErrorMessage, FormControl, FormLabel, toast } from "frappe-ui";
import { __ } from "@/translation";
import AgentSelector from "./components/AgentSelector.vue";
import { useAgentStore } from "@/stores/agent";

interface E {
  (event: "update:step", step: string, team?: string): void;
}

const emit = defineEmits<E>();

const teamsList = inject<any>("teamsData");
const { agents } = useAgentStore();

const isDirty = computed(() => {
  return teamData.value.name || teamData.value.agents.length;
});
const showConfirmDialog = ref({
  show: false,
  title: "",
  message: "",
  onConfirm: () => {},
});

const teamData = ref({
  name: "",
  agents: [],
});

const errors = ref({
  name: "",
  agents: "",
});

const goBack = () => {
  const confirmDialogInfo = {
    show: true,
    title: __("Unsaved changes"),
    message: __(
      "Are you sure you want to go back? Unsaved changes will be lost."
    ),
    onConfirm: goBack,
  };
  if (isDirty.value && !showConfirmDialog.value.show) {
    showConfirmDialog.value = confirmDialogInfo;
    return;
  }

  // Workaround fix for settings modal not closing after going back
  setTimeout(() => {
    emit("update:step", "team-list");
  }, 250);
  showConfirmDialog.value.show = false;
};

const saveTeam = () => {
  validateData();
  if (Object.values(errors.value).some((error) => error)) {
    toast.error(__("Please fill all required fields"));
    return;
  }
  teamsList.insert.submit(
    {
      team_name: teamData.value.name,
      users: teamData.value.agents.map((agent) => ({ user: agent })),
    },
    {
      onSuccess: (data) => {
        toast.success(__("Team created"));
        emit("update:step", "team-edit", data.name);
      },
    }
  );
};

const validateData = (key?: string) => {
  const validateField = (field: string) => {
    if (key && field !== key) return;

    switch (field) {
      case "name":
        teamData.value.name?.length == 0
          ? (errors.value.name = "Name is required")
          : (errors.value.name = "");
        break;
      case "agents":
        teamData.value.agents.length == 0
          ? (errors.value.agents = "At least one team member is required")
          : (errors.value.agents = "");
        break;
    }
  };

  if (key) {
    validateField(key);
  } else {
    (Object.keys(errors.value) as string[]).forEach(validateField);
  }

  return errors.value;
};

onMounted(() => {
  if (agents.loading || agents.data?.length || agents.list.promise) {
    return;
  }
  agents.fetch();
});
</script>
