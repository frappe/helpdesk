<template>
  <div
    v-if="getAssignmentRuleData.loading"
    class="flex items-center h-full justify-center"
  >
    <LoadingIndicator class="w-4" />
  </div>
  <div
    v-if="!getAssignmentRuleData.loading"
    class="sticky top-0 z-10 bg-white pb-6 px-10 py-8"
  >
    <div class="flex items-center justify-between w-full">
      <div class="flex items-center gap-2">
        <Button
          variant="ghost"
          icon-left="chevron-left"
          :label="
            assignmentRuleData.assignmentRuleName || 'New Assignment Rule'
          "
          size="md"
          @click="goBack()"
          class="cursor-pointer -ml-4 hover:bg-transparent focus:bg-transparent focus:outline-none focus:ring-0 focus:ring-offset-0 focus-visible:none active:bg-transparent active:outline-none active:ring-0 active:ring-offset-0 active:text-ink-gray-5 font-semibold text-xl hover:opacity-70 !pr-0 !max-w-96 !justify-start"
        />
        <Badge
          :variant="'subtle'"
          :theme="'orange'"
          size="sm"
          :label="__('Unsaved')"
          v-if="isDirty"
        />
      </div>
      <div class="flex items-center gap-4">
        <div
          class="flex items-center justify-between gap-2"
          @click="assignmentRuleData.disabled = !assignmentRuleData.disabled"
        >
          <Switch size="sm" :model-value="!assignmentRuleData.disabled" />
          <span class="text-sm text-ink-gray-7">{{ __("Enabled") }}</span>
        </div>
        <Button
          :disabled="Boolean(!isDirty && assignmentRulesActiveScreen.data)"
          :label="__('Save')"
          theme="gray"
          variant="solid"
          @click="saveAssignmentRule()"
          :loading="isLoading || getAssignmentRuleData.loading"
        />
      </div>
    </div>
  </div>
  <div v-if="!getAssignmentRuleData.loading" class="overflow-y-auto px-10 pb-8">
    <div class="grid grid-cols-2 gap-5">
      <div>
        <FormControl
          :type="'text'"
          size="sm"
          variant="subtle"
          placeholder="Name"
          label="Name"
          v-model="assignmentRuleData.assignmentRuleName"
          required
          maxlength="50"
          @change="validateAssignmentRule('assignmentRuleName')"
        />
        <ErrorMessage
          :message="assignmentRulesErrors.assignmentRuleName"
          class="mt-2"
        />
      </div>
      <div class="flex flex-col gap-1.5">
        <FormLabel label="Priority" />
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
          maxlength="250"
          @change="validateAssignmentRule('description')"
          v-model="assignmentRuleData.description"
        />
        <ErrorMessage
          :message="assignmentRulesErrors.description"
          class="mt-2"
        />
      </div>
    </div>
    <hr class="my-8" />
    <div>
      <div class="flex flex-col gap-1">
        <span class="text-lg font-semibold text-ink-gray-8">{{
          __("Assignment condition")
        }}</span>
        <div class="flex items-center justify-between gap-6">
          <span class="text-p-sm text-ink-gray-6">
            {{
              __("Choose which tickets are affected by this assignment rule.")
            }}
            <a
              class="font-medium underline"
              href="https://docs.frappe.io/helpdesk/assignment-rule"
              target="_blank"
              >{{ __("Learn about conditions") }}</a
            >
          </span>
          <div v-if="isOldSla && assignmentRulesActiveScreen.data">
            <Popover trigger="hover" :hoverDelay="0.25" placement="top-end">
              <template #target>
                <div
                  class="text-sm text-ink-gray-6 flex gap-1 cursor-default text-nowrap flex items-center"
                >
                  <span>{{ __("Old Condition") }}</span>
                  <FeatherIcon name="info" class="size-4" />
                </div>
              </template>
              <template #body-main>
                <div
                  class="text-sm text-ink-gray-6 p-2 bg-white rounded-md max-w-96 text-wrap whitespace-pre-wrap leading-5"
                >
                  <code>{{ assignmentRuleData.assignCondition }}</code>
                </div>
              </template>
            </Popover>
          </div>
        </div>
      </div>
      <div class="mt-5">
        <div
          class="flex flex-col gap-3 items-center text-center text-ink-gray-7 text-sm mb-2 border border-gray-300 rounded-md p-3 py-4"
          v-if="!useNewUI && assignmentRuleData.assignCondition"
        >
          <span class="text-p-sm">
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
          :conditions="assignmentRuleData.assignConditionJson"
          name="assignCondition"
          :errors="assignmentRulesErrors.assignConditionError"
          v-else
        />
        <ErrorMessage
          :message="assignmentRulesErrors.assignCondition"
          class="mt-2"
        />
      </div>
    </div>
    <hr class="my-8" />
    <div>
      <div class="flex flex-col gap-1">
        <span class="text-lg font-semibold text-ink-gray-8">{{
          __("Unassignment condition")
        }}</span>
        <div class="flex items-center justify-between gap-6">
          <span class="text-p-sm text-ink-gray-6">
            {{
              __(
                "Choose which tickets are affected by this un-assignment rule."
              )
            }}
            <a
              class="font-medium underline"
              href="https://docs.frappe.io/helpdesk/assignment-rule"
              target="_blank"
              >{{ __("Learn about conditions") }}</a
            >
          </span>
          <div
            v-if="
              isOldSla &&
              assignmentRulesActiveScreen.data &&
              assignmentRuleData.unassignCondition
            "
          >
            <Popover trigger="hover" :hoverDelay="0.25" placement="top-end">
              <template #target>
                <div
                  class="text-sm text-ink-gray-6 flex gap-1 cursor-default text-nowrap flex items-center"
                >
                  <span> {{ __("Old Condition") }} </span>
                  <FeatherIcon name="info" class="size-4" />
                </div>
              </template>
              <template #body-main>
                <div
                  class="text-sm text-ink-gray-6 p-2 bg-white rounded-md max-w-96 text-wrap whitespace-pre-wrap leading-5"
                >
                  <code>{{ assignmentRuleData.unassignCondition }}</code>
                </div>
              </template>
            </Popover>
          </div>
        </div>
      </div>
      <div class="mt-5">
        <div
          class="flex flex-col gap-3 items-center text-center text-ink-gray-7 text-sm mb-2 border border-gray-300 rounded-md p-3 py-4"
          v-if="!useNewUI && assignmentRuleData.unassignCondition"
        >
          <span class="text-p-sm">
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
          :conditions="assignmentRuleData.unassignConditionJson"
          name="unassignCondition"
          :errors="assignmentRulesErrors.unassignConditionError"
          v-else
        />
      </div>
    </div>
    <hr class="my-8" />
    <div>
      <div class="flex flex-col gap-1">
        <span class="text-lg font-semibold text-ink-gray-8">{{
          __("Assignment Schedule")
        }}</span>
        <span class="text-p-sm text-ink-gray-6">
          {{
            __("Choose the days of the week when this rule should be active.")
          }}
        </span>
      </div>
      <div class="mt-6">
        <AssignmentSchedule />
      </div>
    </div>
    <hr class="my-8" />
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
  call,
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
const isLoading = ref(false);

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
  url: "frappe.client.get",
  params: {
    doctype: "Assignment Rule",
    name: assignmentRulesActiveScreen.value.data?.name,
  },
  auto: Boolean(assignmentRulesActiveScreen.value.data),
  onSuccess(data) {
    assignmentRuleData.value = {
      loading: false,
      assignCondition: data.assign_condition,
      unassignCondition: data.unassign_condition,
      assignConditionJson: JSON.parse(data.assign_condition_json || "[]"),
      unassignConditionJson: JSON.parse(data.unassign_condition_json || "[]"),
      rule: data.rule,
      priority: data.priority,
      users: data.users,
      disabled: data.disabled,
      description: data.description,
      name: data.name,
      assignmentRuleName: data.name,
      assignmentDays: data.assignment_days.map((day) => day.day),
    };

    initialData.value = JSON.stringify(assignmentRuleData.value);

    const conditionsAvailable =
      assignmentRuleData.value.assignCondition?.length > 0;
    const conditionsJsonAvailable =
      assignmentRuleData.value.assignConditionJson?.length > 0;

    if (conditionsAvailable && !conditionsJsonAvailable) {
      useNewUI.value = false;
      isOldSla.value = true;
    } else {
      useNewUI.value = true;
      isOldSla.value = false;
    }
  },
});

if (!assignmentRulesActiveScreen.value.data) {
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
  // Workaround fix for settings modal not closing after going back
  setTimeout(() => {
    assignmentRulesActiveScreen.value = {
      screen: "list",
      data: null,
    };
  }, 250);
  showConfirmDialog.value.show = false;
};

const saveAssignmentRule = () => {
  const validationErrors = validateAssignmentRule(undefined, !useNewUI.value);

  if (Object.values(validationErrors).some((error) => error)) {
    toast.error(
      "Invalid fields, check if all are filled in and values are correct."
    );
    return;
  }

  if (assignmentRulesActiveScreen.value.data) {
    if (isOldSla.value && useNewUI.value) {
      showConfirmDialog.value = {
        show: true,
        title: "Confirm overwrite",
        message:
          "Your old condition will be overwritten. Are you sure you want to save?",
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
  isLoading.value = true;
  createResource({
    url: "frappe.client.insert",
    params: {
      doc: {
        doctype: "Assignment Rule",
        document_type: "HD Ticket",
        rule: assignmentRuleData.value.rule,
        priority: assignmentRuleData.value.priority,
        users: assignmentRuleData.value.users,
        disabled: assignmentRuleData.value.disabled,
        description: assignmentRuleData.value.description,
        assignment_days: assignmentRuleData.value.assignmentDays.map((day) => ({
          day: day,
        })),
        name: assignmentRuleData.value.assignmentRuleName,
        assignment_rule_name: assignmentRuleData.value.assignmentRuleName,
        assign_condition: convertToConditions({
          conditions: assignmentRuleData.value.assignConditionJson,
        }),
        unassign_condition: convertToConditions({
          conditions: assignmentRuleData.value.unassignConditionJson,
        }),
        assign_condition_json: JSON.stringify(
          assignmentRuleData.value.assignConditionJson
        ),
        unassign_condition_json: JSON.stringify(
          assignmentRuleData.value.unassignConditionJson
        ),
      },
    },
    auto: true,
    onSuccess(data) {
      getAssignmentRuleData
        .submit({
          doctype: "Assignment Rule",
          name: data.name,
        })
        .then(() => {
          isLoading.value = false;
          toast.success("Assignment rule created");
        });
      assignmentRulesActiveScreen.value = {
        screen: "view",
        data: data,
      };
    },
    onError: () => {
      isLoading.value = false;
    },
  });
};

const priorityOptions = [
  { label: "Low", value: "0" },
  { label: "Low-Medium", value: "1" },
  { label: "Medium", value: "2" },
  { label: "Medium-High", value: "3" },
  { label: "High", value: "4" },
];

const updateAssignmentRule = async () => {
  isLoading.value = true;

  await call("frappe.client.set_value", {
    doctype: "Assignment Rule",
    document_type: "HD Ticket",
    name: assignmentRuleData.value.name,
    fieldname: {
      rule: assignmentRuleData.value.rule,
      priority: assignmentRuleData.value.priority,
      users: assignmentRuleData.value.users,
      disabled: assignmentRuleData.value.disabled,
      description: assignmentRuleData.value.description,
      assignment_days: assignmentRuleData.value.assignmentDays.map((day) => ({
        day: day,
      })),
      assign_condition: useNewUI.value
        ? convertToConditions({
            conditions: assignmentRuleData.value.assignConditionJson,
          })
        : assignmentRuleData.value.assignCondition,
      unassign_condition: useNewUI.value
        ? convertToConditions({
            conditions: assignmentRuleData.value.unassignConditionJson,
          })
        : assignmentRuleData.value.unassignCondition,
      assign_condition_json: useNewUI.value
        ? JSON.stringify(assignmentRuleData.value.assignConditionJson)
        : null,
      unassign_condition_json: useNewUI.value
        ? JSON.stringify(assignmentRuleData.value.unassignConditionJson)
        : null,
    },
  }).catch((er) => {
    const error =
      er?.messages?.[0] || "Some error occurred while updating assignment rule";
    toast.error(error);
    isLoading.value = false;
  });

  if (
    assignmentRuleData.value.name !==
    assignmentRuleData.value.assignmentRuleName
  ) {
    await call("frappe.client.rename_doc", {
      doctype: "Assignment Rule",
      old_name: assignmentRuleData.value.name,
      new_name: assignmentRuleData.value.assignmentRuleName,
    }).catch(async (er) => {
      const error =
        er?.messages?.[0] ||
        "Some error occurred while renaming assignment rule";
      toast.error(error);
      // Reset assignment rule to previous state
      await getAssignmentRuleData.reload();
      isLoading.value = false;
    });
    await getAssignmentRuleData.submit({
      doctype: "Assignment Rule",
      name: assignmentRuleData.value.assignmentRuleName,
    });
  } else {
    getAssignmentRuleData.reload();
  }

  isLoading.value = false;
  toast.success("Assignment rule updated");
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
