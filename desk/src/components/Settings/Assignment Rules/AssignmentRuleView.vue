<template>
  <div
    v-if="assignmentRuleData.loading"
    class="flex items-center h-full justify-center"
  >
    <LoadingIndicator class="w-4" />
  </div>
  <div
    v-if="!assignmentRuleData.loading"
    class="sticky top-0 z-10 bg-white pb-6 px-10 py-8"
  >
    <div class="flex items-center justify-between w-full">
      <div class="flex items-center gap-4">
        <Button
          variant="ghost"
          icon-left="chevron-left"
          :label="
            assignmentRuleData.assignment_rule_name || 'New Assignment Rule'
          "
          size="md"
          @click="goBack()"
          class="cursor-pointer -ml-4 hover:bg-transparent focus:bg-transparent focus:outline-none focus:ring-0 focus:ring-offset-0 focus-visible:none active:bg-transparent active:outline-none active:ring-0 active:ring-offset-0 active:text-ink-gray-5 font-semibold text-xl !pr-0"
        />
        <Badge
          :variant="'subtle'"
          :theme="'orange'"
          size="sm"
          label="Unsaved changes"
          v-if="isDirty"
        />
      </div>
      <div class="flex items-center gap-4">
        <div
          class="flex items-center justify-between gap-2"
          @click="assignmentRuleData.disabled = !assignmentRuleData.disabled"
        >
          <Switch size="sm" :model-value="!assignmentRuleData.disabled" />
          <span class="text-sm text-ink-gray-7">Enabled</span>
        </div>
        <Button
          :disabled="Boolean(!isDirty && assignmentRulesActiveScreen.data)"
          label="Save"
          theme="gray"
          variant="solid"
          @click="saveAssignmentRule()"
        />
      </div>
    </div>
  </div>
  <div v-if="!assignmentRuleData.loading" class="overflow-y-auto px-10 pb-8">
    <div class="grid grid-cols-2 gap-5">
      <div>
        <FormControl
          :type="'text'"
          size="sm"
          variant="subtle"
          placeholder="Name"
          label="Name"
          v-model="assignmentRuleData.assignment_rule_name"
          required
          @change="validateAssignmentRule('assignment_rule_name')"
        />
        <ErrorMessage
          :message="assignmentRulesErrors.assignment_rule_name"
          class="mt-2"
        />
      </div>
      <div class="flex flex-col gap-1.5">
        <FormLabel label="Default priority" required />
        <Popover>
          <template #target="{ togglePopover }">
            <div
              class="flex items-center justify-between text-base rounded h-7 py-1.5 pl-2 pr-2 border border-[--surface-gray-2] bg-surface-gray-2 placeholder-ink-gray-4 hover:border-outline-gray-modals hover:bg-surface-gray-3 focus:bg-surface-white focus:border-outline-gray-4 focus:shadow-sm focus:ring-0 focus-visible:ring-2 focus-visible:ring-outline-gray-3 text-ink-gray-8 transition-colors w-full dark:[color-scheme:dark] cursor-default"
              @click="togglePopover()"
            >
              <div>
                {{
                  priorityOptions.find(
                    (option) => option.value == assignmentRuleData.priority
                  )?.label
                }}
              </div>
              <FeatherIcon name="chevron-down" class="size-4" />
            </div>
          </template>
          <template #body="{ togglePopover }">
            <div
              class="p-1 text-ink-gray-6 top-1 absolute w-full bg-white shadow-2xl rounded"
            >
              <div
                v-for="option in priorityOptions"
                :key="option.value"
                class="p-2 cursor-pointer hover:bg-gray-50 text-base flex items-center justify-between rounded"
                @click="
                  assignmentRuleData.priority = option.value;
                  togglePopover();
                "
              >
                {{ option.label }}
                <FeatherIcon
                  v-if="assignmentRuleData.priority == option.value"
                  name="check"
                  class="size-4"
                />
              </div>
            </div>
          </template>
        </Popover>
      </div>
      <div>
        <FormControl
          :type="'textarea'"
          size="sm"
          variant="subtle"
          placeholder="Description"
          label="Description"
          required
          @change="validateAssignmentRule('description')"
          v-model="assignmentRuleData.description"
        />
        <ErrorMessage
          :message="assignmentRulesErrors.description"
          class="mt-2"
        />
      </div>
    </div>
    <hr class="my-6" />
    <div>
      <div class="flex flex-col gap-2">
        <span class="text-lg font-semibold text-ink-gray-7"
          >Assignment rule</span
        >
        <div class="flex items-center justify-between gap-6">
          <span class="text-sm text-ink-gray-6">
            Choose which tickets are affected by this assignment rule.
            <a
              class="font-medium underline"
              href="https://docs.frappe.io/helpdesk/assignment-rule"
              target="_blank"
              >Learn about conditions</a
            >
          </span>
          <div v-if="isOldSla && assignmentRulesActiveScreen.data">
            <Popover trigger="hover" :hoverDelay="0.25" placement="top-end">
              <template #target>
                <div
                  class="text-sm text-ink-gray-6 flex gap-1 cursor-default text-nowrap"
                >
                  Old Conditions
                  <FeatherIcon name="info" class="size-4" />
                </div>
              </template>
              <template #body-main>
                <div
                  class="text-sm text-ink-gray-6 p-2 bg-white rounded-md max-w-96 text-wrap whitespace-pre-wrap leading-5"
                >
                  <code>{{ assignmentRuleData.assign_condition }}</code>
                </div>
              </template>
            </Popover>
          </div>
        </div>
      </div>
      <div class="mt-4">
        <div
          class="flex flex-col gap-3 items-center text-center text-ink-gray-7 text-sm mb-2 border border-gray-300 rounded-md p-3 py-4"
          v-if="!useNewUI && assignmentRuleData.assign_condition"
        >
          <span>
            Conditions for this rule were created from
            <a :href="deskUrl" target="_blank" class="underline">desk</a> which
            are not compatible with this UI, you will need to recreate the
            conditions here if you want to manage and add new conditions from
            this UI.
          </span>
          <Button
            label="I understand, add conditions"
            variant="subtle"
            theme="gray"
            @click="useNewUI = true"
          />
        </div>
        <AssignmentRulesSection
          :conditions="assignmentRuleData.assign_condition_json"
          name="assign_condition"
          :errors="assignmentRulesErrors.assign_condition_error"
          v-else
        />
        <ErrorMessage
          :message="assignmentRulesErrors.assign_condition"
          class="mt-2"
        />
      </div>
    </div>
    <hr class="my-6" />
    <div>
      <div class="flex flex-col gap-2">
        <span class="text-lg font-semibold text-ink-gray-7"
          >Unassignment rule</span
        >
        <div class="flex items-center justify-between gap-6">
          <span class="text-sm text-ink-gray-6">
            Choose which tickets are affected by this un-assignment rule.
            <a
              class="font-medium underline"
              href="https://docs.frappe.io/helpdesk/assignment-rule"
              target="_blank"
              >Learn about conditions</a
            >
          </span>
          <div
            v-if="
              isOldSla &&
              assignmentRulesActiveScreen.data &&
              assignmentRuleData.unassign_condition
            "
          >
            <Popover trigger="hover" :hoverDelay="0.25" placement="top-end">
              <template #target>
                <div
                  class="text-sm text-ink-gray-6 flex gap-1 cursor-default text-nowrap"
                >
                  Old Conditions
                  <FeatherIcon name="info" class="size-4" />
                </div>
              </template>
              <template #body-main>
                <div
                  class="text-sm text-ink-gray-6 p-2 bg-white rounded-md max-w-96 text-wrap whitespace-pre-wrap leading-5"
                >
                  <code>{{ assignmentRuleData.unassign_condition }}</code>
                </div>
              </template>
            </Popover>
          </div>
        </div>
      </div>
      <div class="mt-4">
        <div
          class="flex flex-col gap-3 items-center text-center text-ink-gray-7 text-sm mb-2 border border-gray-300 rounded-md p-3 py-4"
          v-if="!useNewUI && assignmentRuleData.unassign_condition"
        >
          <span>
            Conditions for this rule were created from
            <a :href="deskUrl" target="_blank" class="underline">desk</a> which
            are not compatible with this UI, you will need to recreate the
            conditions here if you want to manage and add new conditions from
            this UI.
          </span>
          <Button
            label="I understand, add conditions"
            variant="subtle"
            theme="gray"
            @click="useNewUI = true"
          />
        </div>
        <AssignmentRulesSection
          :conditions="assignmentRuleData.unassign_condition_json"
          name="unassign_condition"
          :errors="assignmentRulesErrors.unassign_condition_error"
          v-else
        />
      </div>
    </div>
    <hr class="my-6" />
    <div>
      <div class="flex flex-col gap-2">
        <span class="text-lg font-semibold text-ink-gray-7"
          >Assignment Schedule</span
        >
        <span class="text-sm text-ink-gray-6">
          Choose the days of the week when this rule should be active.
        </span>
      </div>
      <div class="mt-4">
        <AssignmentSchedule />
      </div>
    </div>
    <hr class="my-6" />
    <AssigneeRules />
  </div>
  <ConfirmDialog
    v-model="showConfirmDialog.show"
    :title="showConfirmDialog.title"
    :message="showConfirmDialog.message"
    :onConfirm="showConfirmDialog.onConfirm"
    :onCancel="() => (showConfirmDialog.show = false)"
  />
</template>

<script setup lang="ts">
import ConfirmDialog from "@/components/ConfirmDialog.vue";
import {
  Badge,
  Button,
  createResource,
  ErrorMessage,
  FormControl,
  FormLabel,
  LoadingIndicator,
  Popover,
  Switch,
  toast,
} from "frappe-ui";
import { onMounted, onUnmounted, ref, watch } from "vue";
import {
  assignmentRuleData,
  assignmentRulesActiveScreen,
  assignmentRulesErrors,
  resetAssignmentRuleData,
  resetAssignmentRuleErrors,
  validateAssignmentRule,
} from "../../../stores/assignmentRules";
import AssigneeRules from "./AssigneeRules.vue";
import AssignmentRulesSection from "./AssignmentRulesSection.vue";
import AssignmentSchedule from "./AssignmentSchedule.vue";
import { convertToConditions } from "@/utils";
import { disableSettingModalOutsideClick } from "../settingsModal";

const isDirty = ref(false);
const initialData = ref(null);

const showConfirmDialog = ref({
  show: false,
  title: "",
  message: "",
  onConfirm: () => {},
});
const useNewUI = ref(true);
const isOldSla = ref(false);
const deskUrl = `${window.location.origin}/app/assignment-rule/${assignmentRulesActiveScreen.value.data?.name}`;

const getAssignmentRuleData = createResource({
  url: "helpdesk.api.assignment_rule.get_assignment_rule",
  params: {
    docname: assignmentRulesActiveScreen.value.data?.name,
  },
  onSuccess(data) {
    assignmentRuleData.value = data;
    assignmentRuleData.value.loading = false;
    initialData.value = JSON.stringify(assignmentRuleData.value);
    const conditionsAvailable =
      assignmentRuleData.value.assign_condition?.length > 0;
    const conditionsJsonAvailable =
      assignmentRuleData.value.assign_condition_json?.length > 0;
    if (conditionsAvailable && !conditionsJsonAvailable) {
      useNewUI.value = false;
      isOldSla.value = true;
    } else {
      useNewUI.value = true;
      isOldSla.value = false;
    }
  },
  transform(data) {
    data.assign_condition_json = JSON.parse(data.assign_condition_json || "[]");
    data.unassign_condition_json = JSON.parse(
      data.unassign_condition_json || "[]"
    );
    data.assignment_rule_name = data.name;
    data.users = data.users.map((user) => {
      return {
        ...user,
        ticketCount:
          data.ticket_counts.find(
            (ticketCount) => ticketCount.user == user.user
          )?.count || 0,
      };
    });
    return data;
  },
  auto: false,
});

if (assignmentRulesActiveScreen.value.data) {
  assignmentRuleData.value.loading = true;
  getAssignmentRuleData.submit();
} else {
  disableSettingModalOutsideClick.value = true;
}

const goBack = () => {
  const confirmDialogInfo = {
    show: true,
    title: "Unsaved changes",
    message: "Are you sure you want to go back? Unsaved changes will be lost.",
    onConfirm: goBack,
  };
  if (isDirty.value && !showConfirmDialog.value.show) {
    showConfirmDialog.value = confirmDialogInfo;
    return;
  }
  if (
    !assignmentRulesActiveScreen.value.data &&
    !showConfirmDialog.value.show
  ) {
    showConfirmDialog.value = confirmDialogInfo;
    return;
  }
  assignmentRulesActiveScreen.value = {
    screen: "list",
    data: null,
  };
};

const saveAssignmentRule = () => {
  const validationErrors = validateAssignmentRule(undefined, !useNewUI.value);

  if (Object.values(validationErrors).some((error) => error)) {
    toast.error("Please provide all required fields");
    return;
  }

  if (assignmentRulesActiveScreen.value.data) {
    if (isOldSla.value && useNewUI.value) {
      showConfirmDialog.value = {
        show: true,
        title: "Confirm overwrite",
        message:
          "Your old conditions will be overwritten. Are you sure you want to save?",
        onConfirm: () => {
          updateAssignmentRule();
          showConfirmDialog.value.show = false;
        },
      };
      return;
    }
    updateAssignmentRule();
  } else {
    createAssignmentRule();
  }
};

const createAssignmentRule = () => {
  createResource({
    url: "frappe.client.insert",
    params: {
      doc: {
        ...assignmentRuleData.value,
        name: assignmentRuleData.value.assignment_rule_name,
        doctype: "Assignment Rule",
        document_type: "HD Ticket",
        assign_condition: convertToConditions({
          conditions: assignmentRuleData.value.assign_condition_json,
        }),
        unassign_condition: convertToConditions({
          conditions: assignmentRuleData.value.unassign_condition_json,
        }),
        assign_condition_json: JSON.stringify(
          assignmentRuleData.value.assign_condition_json
        ),
        unassign_condition_json: JSON.stringify(
          assignmentRuleData.value.unassign_condition_json
        ),
      },
    },
    auto: true,
    onSuccess(data) {
      getAssignmentRuleData.submit({
        docname: data.name,
      });
      assignmentRulesActiveScreen.value = {
        screen: "view",
        data: data,
      };
      toast.success("Assignment rule created");
    },
  });
};

const priorityOptions = [
  { label: "Low", value: "0" },
  { label: "Medium-Low", value: "1" },
  { label: "Medium", value: "2" },
  { label: "Medium-High", value: "3" },
  { label: "High", value: "4" },
];

const updateAssignmentRule = async () => {
  createResource({
    url: "helpdesk.api.assignment_rule.save_assignment_rule",
    params: {
      doc: {
        ...assignmentRuleData.value,
        doctype: "Assignment Rule",
        document_type: "HD Ticket",
        assign_condition: useNewUI.value
          ? convertToConditions({
              conditions: assignmentRuleData.value.assign_condition_json,
            })
          : assignmentRuleData.value.assign_condition,
        unassign_condition: useNewUI.value
          ? convertToConditions({
              conditions: assignmentRuleData.value.unassign_condition_json,
            })
          : assignmentRuleData.value.unassign_condition,
        assign_condition_json: useNewUI.value
          ? JSON.stringify(assignmentRuleData.value.assign_condition_json)
          : null,
        unassign_condition_json: useNewUI.value
          ? JSON.stringify(assignmentRuleData.value.unassign_condition_json)
          : null,
      },
    },
    auto: true,
    onSuccess(data) {
      getAssignmentRuleData.submit({
        docname: data.name,
      });
      toast.success("Assignment rule updated");
    },
  });
};

watch(
  assignmentRuleData,
  (newVal) => {
    if (!initialData.value) return;
    isDirty.value = JSON.stringify(newVal) != initialData.value;
    if (isDirty.value) {
      disableSettingModalOutsideClick.value = true;
    } else {
      disableSettingModalOutsideClick.value = false;
    }
  },
  { deep: true }
);

const beforeUnloadHandler = (event) => {
  if (!isDirty.value) return;
  event.preventDefault();
  event.returnValue = true;
};

onMounted(() => {
  addEventListener("beforeunload", beforeUnloadHandler);
});

onUnmounted(() => {
  resetAssignmentRuleErrors();
  resetAssignmentRuleData();
  removeEventListener("beforeunload", beforeUnloadHandler);
  disableSettingModalOutsideClick.value = false;
});
</script>
