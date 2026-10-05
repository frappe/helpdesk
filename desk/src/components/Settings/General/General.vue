<template>
  <SettingsLayoutBase :description="__('Manage general settings of your app.')">
    <template #title>
      <div class="flex items-center gap-2">
        <h1 class="text-md-semibold text-ink-gray-8">
          {{ __("General") }}
        </h1>
        <UnsavedBadge :show="isDirty" />
      </div>
    </template>
    <template #header-actions>
      <Transition name="fade">
        <div v-if="isDirty">
          <Button
            :label="__('Save')"
            variant="solid"
            @click="saveSettings"
            :loading="saveSettingsResource.loading"
          />
        </div>
      </Transition>
    </template>
    <template #content>
      <div
        v-if="settingsDataResource.loading && !settingsDataResource.data"
        class="flex items-center justify-center absolute inset-x-0 top-5.5 bottom-0"
      >
        <LoadingIndicator class="w-4" />
      </div>
      <div v-else>
        <Branding />
        <hr class="my-8" />
        <TicketSettings />
        <hr class="my-8" />
        <WorkflowSettings />
      </div>
    </template>
  </SettingsLayoutBase>
</template>

<script setup lang="ts">
import SettingsLayoutBase from "@/components/layouts/SettingsLayoutBase.vue";
import UnsavedBadge from "@/components/UnsavedBadge.vue";
import { useConfigStore } from "@/stores/config";
import { __ } from "@/translation";
import { HDSettings, HDSettingsSymbol } from "@/types";
import {
  Button,
  createResource,
  LoadingIndicator,
  toast,
} from "frappe-ui";
import { provide, ref, watch } from "vue";
import { disableSettingModalOutsideClick } from "../settingsModal";
import Branding from "./components/Branding.vue";
import TicketSettings from "./components/TicketSettings.vue";
import WorkflowSettings from "./components/WorkflowSettings.vue";

const configStore = useConfigStore();

const isDirty = ref(false);
const initialData = ref<null | string>(null);
const settingsData = ref({
  brandName: "",
  brandLogo: "",
  favicon: "",
  autoCloseAfterDays: "",
  autoCloseStatus: "",
  autoCloseTickets: "",
  assignWithinTeam: false,
  doNotRestrictTicketsWithoutAnAgentGroup: false,
  restrictTicketsByAgentGroup: false,
  updateStatusTo: "",
  autoUpdateStatus: false,
  isFeedbackMandatory: false,
  enableCommentReactions: false,
  defaultTicketType: "",
  skipEmailWorkflow: false,
  disableSavedRepliesGlobalScope: false,
  enableOutsideHoursBanner: false,
  outsideWorkingHoursBannerMessage: "",
});

provide(HDSettingsSymbol, settingsData);

const settingsDataResource = createResource({
  url: "frappe.client.get",
  params: {
    doctype: "HD Settings",
    name: "HD Settings",
  },
  auto: true,
  onSuccess(data: HDSettings) {
    settingsData.value = transformData(data);
    initialData.value = JSON.stringify(settingsData.value);
  },
});

const saveSettingsResource = createResource({
  url: "frappe.client.set_value",
  makeParams() {
    return {
      doctype: "HD Settings",
      name: "HD Settings",
      fieldname: {
        brand_name: settingsData.value.brandName,
        auto_close_after_days: Number(settingsData.value.autoCloseAfterDays),
        auto_close_status: settingsData.value.autoCloseStatus,
        auto_close_tickets: settingsData.value.autoCloseTickets,
        assign_within_team: settingsData.value.assignWithinTeam,
        do_not_restrict_tickets_without_an_agent_group:
          settingsData.value.doNotRestrictTicketsWithoutAnAgentGroup,
        restrict_tickets_by_agent_group:
          settingsData.value.restrictTicketsByAgentGroup,
        update_status_to: settingsData.value.updateStatusTo,
        auto_update_status: settingsData.value.autoUpdateStatus,
        is_feedback_mandatory: settingsData.value.isFeedbackMandatory,
        enable_comment_reactions: settingsData.value.enableCommentReactions,
        default_ticket_type: settingsData.value.defaultTicketType,
        skip_email_workflow: settingsData.value.skipEmailWorkflow,
        disable_saved_replies_global_scope:
          settingsData.value.disableSavedRepliesGlobalScope,

        enable_outside_hours_banner:
          settingsData.value.enableOutsideHoursBanner,
        outside_working_hours_message:
          settingsData.value.outsideWorkingHoursBannerMessage,
      },
    };
  },
  onSuccess(data: HDSettings) {
    settingsData.value = transformData(data);
    initialData.value = JSON.stringify(settingsData.value);
    configStore.configResource.reload();
  },
});

const transformData = (data: any) => {
  return {
    brandName: data.brand_name,
    brandLogo: data.brand_logo,
    favicon: data.favicon,
    autoCloseAfterDays: data.auto_close_after_days,
    autoCloseStatus: data.auto_close_status,
    autoCloseTickets: data.auto_close_tickets,
    assignWithinTeam: Boolean(data.assign_within_team),
    doNotRestrictTicketsWithoutAnAgentGroup: Boolean(
      data.do_not_restrict_tickets_without_an_agent_group
    ),
    restrictTicketsByAgentGroup: Boolean(data.restrict_tickets_by_agent_group),
    updateStatusTo: data.update_status_to,
    autoUpdateStatus: data.auto_update_status,
    isFeedbackMandatory: Boolean(data.is_feedback_mandatory),
    enableCommentReactions: Boolean(data.enable_comment_reactions),
    defaultTicketType: data.default_ticket_type,
    skipEmailWorkflow: Boolean(data.skip_email_workflow),
    disableSavedRepliesGlobalScope: Boolean(
      data.disable_saved_replies_global_scope
    ),
    enableOutsideHoursBanner: Boolean(data.enable_outside_hours_banner),
    outsideWorkingHoursBannerMessage: data.outside_working_hours_message || "",
  };
};

const saveSettings = async () => {
  if (
    settingsData.value.restrictTicketsByAgentGroup &&
    !settingsData.value.doNotRestrictTicketsWithoutAnAgentGroup &&
    !settingsData.value.assignWithinTeam
  ) {
    toast.error(
      __(
        "Please select at least one restriction option for teams in the settings."
      )
    );
    return;
  }
  const promises = [];
  if (isDirty.value) {
    promises.push(saveSettingsResource.submit());
  }
  await Promise.allSettled(promises).then(() => {
    toast.success(__("Settings updated"));
  });
};

const toggleFieldnames = {
  isFeedbackMandatory: "is_feedback_mandatory",
  enableCommentReactions: "enable_comment_reactions",
  disableSavedRepliesGlobalScope: "disable_saved_replies_global_scope",
  skipEmailWorkflow: "skip_email_workflow",
} as const;
const toggleFields = Object.keys(toggleFieldnames) as Array<
  keyof typeof toggleFieldnames
>;

// Toggles save on their own, so they never carry unsaved text fields along.
const saveTogglesResource = createResource({
  url: "frappe.client.set_value",
  makeParams: (values: Record<string, unknown>) => ({
    doctype: "HD Settings",
    name: "HD Settings",
    fieldname: Object.fromEntries(
      toggleFields.map((f) => [toggleFieldnames[f], values[f]])
    ),
  }),
});
let pendingToggleSave = Promise.resolve();

function currentToggles() {
  return Object.fromEntries(
    toggleFields.map((f) => [f, settingsData.value[f]])
  );
}

async function saveToggles(sent: Record<string, unknown>) {
  try {
    await saveTogglesResource.submit(sent);
    markTogglesSaved(sent);
    toast.success(__("Settings updated"));
  } catch {
    revertToggles(sent);
  }
}

function markTogglesSaved(sent: Record<string, unknown>) {
  const initial = JSON.parse(initialData.value!);
  toggleFields.forEach((f) => (initial[f] = sent[f]));
  initialData.value = JSON.stringify(initial);
  configStore.configResource.reload();
}

// Undo only what the failed request sent; a toggle changed since keeps its queued save.
function revertToggles(sent: Record<string, unknown>) {
  const initial = JSON.parse(initialData.value!);
  toggleFields
    .filter((f) => settingsData.value[f] === sent[f])
    .forEach((f) => (settingsData.value[f] = initial[f]));
}

// Track dirty state for non-toggle fields only
watch(
  settingsData,
  (data) => {
    if (!initialData.value) return;
    const initial = JSON.parse(initialData.value);
    isDirty.value = Object.keys(data).some(
      (key) =>
        !(toggleFields as string[]).includes(key) &&
        JSON.stringify(data[key as keyof typeof data]) !==
          JSON.stringify(initial[key])
    );
    disableSettingModalOutsideClick.value = isDirty.value;
  },
  { deep: true }
);

// Queue toggle saves: parallel writes to the single doc fail with a 417.
watch(
  () => toggleFields.map((f) => settingsData.value[f]),
  (newVals) => {
    if (!initialData.value) return;
    const initial = JSON.parse(initialData.value);
    if (!newVals.some((v, i) => v !== initial[toggleFields[i]])) return;
    pendingToggleSave = pendingToggleSave.then(() =>
      saveToggles(currentToggles())
    );
  }
);
</script>
